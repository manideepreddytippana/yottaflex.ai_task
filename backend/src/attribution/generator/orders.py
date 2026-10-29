"""Deterministic generation of Orders and Order Event History."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
import random
from typing import Any

from src.attribution.ids import DeterministicIDGenerator


def generate_orders(
    opportunities: list[dict[str, Any]],
    leads: list[dict[str, Any]],
    id_gen: DeterministicIDGenerator,
    rng: random.Random,
    reporting_currency: str = "INR",
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Generate orders from won opportunities and their immutable order event streams."""
    orders: list[dict[str, Any]] = []
    order_events: list[dict[str, Any]] = []

    # Map leads to contacts
    lead_to_contact: dict[str, str] = {l["lead_id"]: l["contact_id"] for l in leads}

    won_opportunities = [o for o in opportunities if o["status"] == "WON" and o["closed_at"] is not None]
    
    txn_counter = 1

    for opp in won_opportunities:
        oid = id_gen.order_id()
        opp_id = opp["opportunity_id"]
        contact_id = lead_to_contact.get(opp["lead_id"])
        if not contact_id:
            continue

        closed_at = datetime.fromisoformat(opp["closed_at"])
        # Ordered within hours or up to 2 days of deal closing
        ordered_at = closed_at + timedelta(hours=rng.randint(1, 48))

        gross_val = Decimal(str(opp["actual_closed_value"] or opp["expected_value"])).quantize(Decimal("0.01"))
        
        # 95% fully paid, 3% refunded, 2% partially refunded
        r = rng.random()
        if r < 0.95:
            status = "PAID"
            refund = Decimal("0.00")
        elif r < 0.98:
            status = "REFUNDED"
            refund = gross_val
        else:
            status = "PARTIALLY_REFUNDED"
            refund = (gross_val * Decimal("0.25")).quantize(Decimal("0.01"))

        net_rev = (gross_val - refund).quantize(Decimal("0.01"))
        txn_key = f"TXN-2026-{txn_counter:06d}"
        txn_counter += 1

        orders.append({
            "order_id": oid,
            "opportunity_id": opp_id,
            "contact_id": contact_id,
            "ordered_at": ordered_at.isoformat(),
            "status": status,
            "gross_amount": float(gross_val),
            "refund_amount": float(refund),
            "net_revenue": float(net_rev),
            "currency": reporting_currency,
            "economic_transaction_key": txn_key,
            "issue_type": None,
        })

        # Order events
        # 1. Event: Created
        evt1_id = id_gen.order_event_id()
        order_events.append({
            "order_event_id": evt1_id,
            "order_id": oid,
            "event_type": "CREATED",
            "old_status": None,
            "new_status": "PENDING",
            "occurred_at": ordered_at.isoformat(),
            "event_payload": {"gross_amount": float(gross_val)},
            "run_id": None,
        })

        # 2. Event: Paid
        evt2_id = id_gen.order_event_id()
        paid_at = ordered_at + timedelta(minutes=rng.randint(5, 60))
        order_events.append({
            "order_event_id": evt2_id,
            "order_id": oid,
            "event_type": "PAID",
            "old_status": "PENDING",
            "new_status": "PAID",
            "occurred_at": paid_at.isoformat(),
            "event_payload": {"payment_reference": f"PAY-{oid}"},
            "run_id": None,
        })

        # 3. Event: Refunded (if applicable)
        if status in ("REFUNDED", "PARTIALLY_REFUNDED"):
            evt3_id = id_gen.order_event_id()
            refund_at = paid_at + timedelta(days=rng.randint(2, 10))
            order_events.append({
                "order_event_id": evt3_id,
                "order_id": oid,
                "event_type": "REFUNDED",
                "old_status": "PAID",
                "new_status": status,
                "occurred_at": refund_at.isoformat(),
                "event_payload": {"refund_amount": float(refund), "net_revenue": float(net_rev)},
                "run_id": None,
            })

    orders.sort(key=lambda o: (o["ordered_at"], o["order_id"]))
    order_events.sort(key=lambda e: (e["occurred_at"], e["order_event_id"]))
    return orders, order_events

