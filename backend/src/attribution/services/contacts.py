"""Customer journey reconstruction and timeline explorer service."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import select

from src.attribution.db.models import (
    Campaign,
    Channel,
    Contact,
    Lead,
    Opportunity,
    OpportunityEvent,
    Order,
    OrderEvent,
    Touchpoint,
    WebSession,
)
from src.attribution.db.session import get_db_session
from src.attribution.services.base import BaseService


class ContactService(BaseService):
    """Service for retrieving customer records and reconstructing multi-channel journey timelines."""

    def get_customer_journey(self, contact_id: str) -> Optional[dict[str, Any]]:
        """Reconstruct chronological multi-channel journey stream for a contact with eligibility flags."""
        with get_db_session() as session:
            contact = session.scalar(select(Contact).where(Contact.contact_id == contact_id))
            if not contact:
                return None

            timeline: list[dict[str, Any]] = []

            # 1. Touchpoints
            touchpoints = session.scalars(
                select(Touchpoint).where(Touchpoint.contact_id == contact_id).order_by(Touchpoint.occurred_at)
            ).all()

            # Find earliest conversion order date for this contact
            orders = session.scalars(
                select(Order).where(Order.contact_id == contact_id).order_by(Order.ordered_at)
            ).all()
            first_order_date = orders[0].ordered_at if orders else None

            for tp in touchpoints:
                is_eligible = True
                exclusion_reason = None

                # Check if after conversion
                if first_order_date and tp.occurred_at > first_order_date:
                    is_eligible = False
                    exclusion_reason = "Post-conversion interaction: occurred after order placed"

                tp_channel = session.scalar(select(Channel).where(Channel.channel_id == tp.channel_id)) if tp.channel_id else None
                tp_campaign = session.scalar(select(Campaign).where(Campaign.campaign_id == tp.campaign_id)) if tp.campaign_id else None

                timeline.append({
                    "event_id": tp.touchpoint_id,
                    "event_type": "touchpoint",
                    "occurred_at": tp.occurred_at,
                    "title": f"Touchpoint: {tp.touch_type} on {tp_channel.name if tp_channel else 'Unknown'}",
                    "details": {
                        "campaign_id": tp.campaign_id,
                        "campaign_name": tp_campaign.name if tp_campaign else None,
                        "interaction_type": tp.touch_type,
                        "touch_mode": tp.touch_mode,
                        "identity_evidence": tp.identity_evidence,
                    },
                    "is_eligible_touch": is_eligible,
                    "exclusion_reason": exclusion_reason,
                })

            # 2. Web Sessions
            sessions = session.scalars(
                select(WebSession).where(WebSession.contact_id == contact_id).order_by(WebSession.started_at)
            ).all()
            for s in sessions:
                timeline.append({
                    "event_id": s.session_id,
                    "event_type": "session",
                    "occurred_at": s.started_at,
                    "title": f"Web Session ({s.landing_path or '/'})",
                    "details": {
                        "landing_path": s.landing_path,
                        "is_anonymous": s.is_anonymous,
                        "identity_evidence": s.identity_evidence,
                    },
                    "is_eligible_touch": None,
                    "exclusion_reason": None,
                })

            # 3. Leads
            leads = session.scalars(
                select(Lead).where(Lead.contact_id == contact_id).order_by(Lead.created_at)
            ).all()
            for ld in leads:
                timeline.append({
                    "event_id": ld.lead_id,
                    "event_type": "lead",
                    "occurred_at": ld.created_at,
                    "title": f"Lead Created ({ld.status})",
                    "details": {
                        "status": ld.status,
                        "qualification_at": ld.qualification_at.isoformat() if ld.qualification_at else None,
                    },
                    "is_eligible_touch": None,
                    "exclusion_reason": None,
                })

            # 4. Opportunities
            opps = session.scalars(
                select(Opportunity)
                .join(Lead, Opportunity.lead_id == Lead.lead_id)
                .where(Lead.contact_id == contact_id)
                .order_by(Opportunity.created_at)
            ).all()
            for opp in opps:
                timeline.append({
                    "event_id": opp.opportunity_id,
                    "event_type": "opportunity",
                    "occurred_at": opp.created_at,
                    "title": f"Opportunity Created ({opp.status})",
                    "details": {
                        "status": opp.status,
                        "expected_value": str(opp.expected_value),
                        "closed_at": opp.closed_at.isoformat() if opp.closed_at else None,
                    },
                    "is_eligible_touch": None,
                    "exclusion_reason": None,
                })

                # Opp Events
                opp_events = session.scalars(
                    select(OpportunityEvent).where(OpportunityEvent.opportunity_id == opp.opportunity_id).order_by(OpportunityEvent.occurred_at)
                ).all()
                for oe in opp_events:
                    timeline.append({
                        "event_id": oe.opportunity_event_id,
                        "event_type": "event",
                        "occurred_at": oe.occurred_at,
                        "title": f"Opportunity State Change: {oe.old_status} -> {oe.new_status}",
                        "details": oe.event_payload or {},
                        "is_eligible_touch": None,
                        "exclusion_reason": None,
                    })

            # 5. Orders
            total_attributed_spend = Decimal("0.00")
            for o in orders:
                timeline.append({
                    "event_id": o.order_id,
                    "event_type": "order",
                    "occurred_at": o.ordered_at,
                    "title": f"Order Placed: #{o.order_id} ({o.status})",
                    "details": {
                        "gross_amount": str(o.gross_amount),
                        "net_revenue": str(o.net_revenue),
                        "currency": o.currency,
                        "economic_transaction_key": o.economic_transaction_key,
                    },
                    "is_eligible_touch": None,
                    "exclusion_reason": None,
                })

                # Order Events
                o_events = session.scalars(
                    select(OrderEvent).where(OrderEvent.order_id == o.order_id).order_by(OrderEvent.occurred_at)
                ).all()
                for oev in o_events:
                    timeline.append({
                        "event_id": oev.order_event_id,
                        "event_type": "event",
                        "occurred_at": oev.occurred_at,
                        "title": f"Order Event: {oev.event_type} ({oev.new_status})",
                        "details": oev.event_payload or {},
                        "is_eligible_touch": None,
                        "exclusion_reason": None,
                    })

            # Sort chronological
            timeline.sort(key=lambda x: x["occurred_at"])

            return {
                "contact_id": contact.contact_id,
                "full_name": f"Contact {contact.contact_id}",
                "email": f"{contact.contact_id.lower()}@synthetic.example.com",
                "lifecycle_stage": contact.customer_segment or "CUSTOMER",
                "total_touchpoints": len(touchpoints),
                "total_orders": len(orders),
                "total_spend_attributed": total_attributed_spend,
                "timeline": timeline,
            }

