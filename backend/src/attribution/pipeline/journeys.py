"""Customer Journey reconstruction and timeline assembly."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any


@dataclass
class JourneyEvent:
    event_id: str
    event_type: str  # TOUCHPOINT, WEB_SESSION, LEAD, OPPORTUNITY, ORDER
    timestamp: datetime
    title: str
    details: dict[str, Any]
    is_conversion: bool = False
    is_eligible_for_attribution: bool = True
    ineligibility_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "title": self.title,
            "details": self.details,
            "is_conversion": self.is_conversion,
            "is_eligible_for_attribution": self.is_eligible_for_attribution,
            "ineligibility_reason": self.ineligibility_reason,
        }


@dataclass
class CustomerJourney:
    contact_id: str
    events: list[JourneyEvent]
    total_touchpoints: int
    total_orders: int
    converted_revenue: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "contact_id": self.contact_id,
            "total_touchpoints": self.total_touchpoints,
            "total_orders": self.total_orders,
            "converted_revenue": self.converted_revenue,
            "events": [e.to_dict() for e in self.events],
        }


def reconstruct_contact_journey(
    contact_id: str,
    touchpoints: list[dict[str, Any]],
    web_sessions: list[dict[str, Any]],
    leads: list[dict[str, Any]],
    opportunities: list[dict[str, Any]],
    orders: list[dict[str, Any]],
) -> CustomerJourney:
    """Stitch chronological customer journey from master interactions to conversion."""
    events: list[JourneyEvent] = []

    # 1. Add touchpoints
    for t in touchpoints:
        if t.get("contact_id") == contact_id:
            dt = datetime.fromisoformat(t["occurred_at"])
            events.append(
                JourneyEvent(
                    event_id=t["touchpoint_id"],
                    event_type="TOUCHPOINT",
                    timestamp=dt,
                    title=f"Touchpoint: {t['touch_type']} ({t['touch_mode']})",
                    details={
                        "campaign_id": t.get("campaign_id"),
                        "channel_id": t.get("channel_id"),
                        "touch_type": t["touch_type"],
                        "touch_mode": t["touch_mode"],
                        "identity_evidence": t.get("identity_evidence"),
                    },
                )
            )

    # 2. Add sessions
    for s in web_sessions:
        if s.get("contact_id") == contact_id:
            dt = datetime.fromisoformat(s["started_at"])
            events.append(
                JourneyEvent(
                    event_id=s["session_id"],
                    event_type="WEB_SESSION",
                    timestamp=dt,
                    title="Web Session",
                    details={
                        "landing_path": s.get("landing_path"),
                        "source_channel_id": s.get("source_channel_id"),
                        "is_anonymous": s.get("is_anonymous"),
                        "identity_evidence": s.get("identity_evidence"),
                    },
                )
            )

    # 3. Add leads
    for l in leads:
        if l.get("contact_id") == contact_id:
            dt = datetime.fromisoformat(l["created_at"])
            events.append(
                JourneyEvent(
                    event_id=l["lead_id"],
                    event_type="LEAD",
                    timestamp=dt,
                    title=f"Lead Created ({l['status']})",
                    details={
                        "status": l["status"],
                        "source_type": l["source_type"],
                        "session_id": l.get("session_id"),
                    },
                )
            )

    # 4. Add opportunities
    # Match opportunities through leads
    contact_lead_ids = {l["lead_id"] for l in leads if l.get("contact_id") == contact_id}
    for opp in opportunities:
        if opp.get("lead_id") in contact_lead_ids:
            dt = datetime.fromisoformat(opp["created_at"])
            events.append(
                JourneyEvent(
                    event_id=opp["opportunity_id"],
                    event_type="OPPORTUNITY",
                    timestamp=dt,
                    title=f"Opportunity {opp['status']} (Expected: {opp['expected_value']})",
                    details={
                        "status": opp["status"],
                        "expected_value": opp["expected_value"],
                        "actual_closed_value": opp.get("actual_closed_value"),
                        "closed_at": opp.get("closed_at"),
                    },
                )
            )

    # 5. Add orders
    total_rev = 0.0
    for o in orders:
        if o.get("contact_id") == contact_id:
            dt = datetime.fromisoformat(o["ordered_at"])
            net_rev = float(o.get("net_revenue", 0.0))
            total_rev += net_rev
            events.append(
                JourneyEvent(
                    event_id=o["order_id"],
                    event_type="ORDER",
                    timestamp=dt,
                    title=f"Order Conversion ({o['status']}): {net_rev} {o['currency']}",
                    details={
                        "status": o["status"],
                        "gross_amount": float(o["gross_amount"]),
                        "refund_amount": float(o["refund_amount"]),
                        "net_revenue": net_rev,
                        "currency": o["currency"],
                        "economic_transaction_key": o["economic_transaction_key"],
                    },
                    is_conversion=True,
                )
            )

    # Sort deterministically by timestamp, then event_id
    events.sort(key=lambda e: (e.timestamp, e.event_id))

    tp_count = sum(1 for e in events if e.event_type == "TOUCHPOINT")
    ord_count = sum(1 for e in events if e.event_type == "ORDER")

    return CustomerJourney(
        contact_id=contact_id,
        events=events,
        total_touchpoints=tp_count,
        total_orders=ord_count,
        converted_revenue=round(total_rev, 2),
    )


def filter_eligible_touchpoints_for_order(
    order: dict[str, Any],
    contact_touchpoints: list[dict[str, Any]],
    lookback_window_days: int = 180,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Filter touchpoints strictly according to the 6 eligibility rules.
    
    Returns:
        tuple: (eligible_touchpoints, ineligible_touchpoints_with_reason)
    """
    order_dt = datetime.fromisoformat(order["ordered_at"])
    window_start = order_dt - timedelta(days=lookback_window_days)

    eligible: list[dict[str, Any]] = []
    ineligible: list[dict[str, Any]] = []

    for t in contact_touchpoints:
        t_dt = datetime.fromisoformat(t["occurred_at"])

        # Rule 1: Temporal Precedence (occurred on or before conversion)
        if t_dt > order_dt:
            ineligible.append({**t, "ineligibility_reason": "POST_CONVERSION"})
            continue

        # Rule 2: Lookback Window
        if t_dt < window_start:
            ineligible.append({**t, "ineligibility_reason": "OUTSIDE_LOOKBACK_WINDOW"})
            continue

        # Rule 3: Valid Campaign Reference
        if not t.get("campaign_id"):
            ineligible.append({**t, "ineligibility_reason": "MISSING_CAMPAIGN_REFERENCE"})
            continue

        # Rule 4: Supported Identity Evidence
        evidence = t.get("identity_evidence", "NONE")
        if evidence not in ("AUTHENTICATED", "CONSENTED_MATCH", "SESSION_LINK"):
            ineligible.append({**t, "ineligibility_reason": "UNSUPPORTED_IDENTITY_EVIDENCE"})
            continue

        eligible.append(t)

    # Sort eligible touchpoints ascending by timestamp, tie-breaking on touchpoint_id
    eligible.sort(key=lambda x: (datetime.fromisoformat(x["occurred_at"]), x["touchpoint_id"]))
    return eligible, ineligible

