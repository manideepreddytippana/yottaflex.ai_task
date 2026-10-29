"""Deterministic generation of Sales Opportunities and Opportunity Lifecycle Events."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
import random
from typing import Any

from src.attribution.ids import DeterministicIDGenerator


OPP_STATUSES = ["OPEN", "QUALIFIED", "PROPOSAL", "WON", "LOST", "CANCELLED"]


def generate_opportunities(
    target_count: int,
    leads: list[dict[str, Any]],
    id_gen: DeterministicIDGenerator,
    rng: random.Random,
    reporting_currency: str = "INR",
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Generate opportunities and their append-only lifecycle event history."""
    opportunities: list[dict[str, Any]] = []
    opportunity_events: list[dict[str, Any]] = []

    # Filter qualified or eligible leads
    qual_leads = [l for l in leads if l["status"] in ("QUALIFIED", "CONVERTED", "CLOSED")]
    if not qual_leads:
        qual_leads = leads

    for i in range(target_count):
        oid = id_gen.opportunity_id()
        lead = qual_leads[i % len(qual_leads)]
        lead_created = datetime.fromisoformat(lead["created_at"])

        opp_created = lead_created + timedelta(days=rng.randint(1, 14), hours=rng.randint(1, 12))
        expected_val = Decimal(str(rng.randint(25000, 250000)))
        
        # Status distribution: roughly 35% WON, 35% LOST, 20% OPEN/PROPOSAL, 10% CANCELLED
        r = rng.random()
        if r < 0.35:
            status = "WON"
        elif r < 0.70:
            status = "LOST"
        elif r < 0.85:
            status = "PROPOSAL"
        elif r < 0.95:
            status = "OPEN"
        else:
            status = "CANCELLED"

        closed_at = None
        actual_val = None

        if status in ("WON", "LOST", "CANCELLED"):
            close_time = opp_created + timedelta(days=rng.randint(7, 45), hours=rng.randint(1, 12))
            closed_at = close_time.isoformat()
            if status == "WON":
                # Slight variation in final deal value
                ratio = Decimal(str(rng.uniform(0.9, 1.1))).quantize(Decimal("0.01"))
                actual_val = (expected_val * ratio).quantize(Decimal("0.01"))

        opportunities.append({
            "opportunity_id": oid,
            "lead_id": lead["lead_id"],
            "created_at": opp_created.isoformat(),
            "expected_value": float(expected_val),
            "currency": reporting_currency,
            "status": status,
            "closed_at": closed_at,
            "actual_closed_value": float(actual_val) if actual_val is not None else None,
            "issue_type": None,
        })

        # Append-only lifecycle events
        # 1. Event: Created
        evt1_id = id_gen.opportunity_event_id()
        opportunity_events.append({
            "opportunity_event_id": evt1_id,
            "opportunity_id": oid,
            "event_type": "CREATED",
            "old_status": None,
            "new_status": "OPEN",
            "occurred_at": opp_created.isoformat(),
            "event_payload": {"stage": "discovery", "initial_value": float(expected_val)},
            "run_id": None,
        })

        # 2. Progression events
        if status in ("PROPOSAL", "WON", "LOST", "CANCELLED"):
            if status == "PROPOSAL":
                prop_time = opp_created + timedelta(days=rng.randint(3, 10))
            else:
                close_dt = datetime.fromisoformat(closed_at)
                total_secs = max(7200, int((close_dt - opp_created).total_seconds()))
                prop_time = opp_created + timedelta(seconds=rng.randint(3600, total_secs - 3600))

            evt2_id = id_gen.opportunity_event_id()
            opportunity_events.append({
                "opportunity_event_id": evt2_id,
                "opportunity_id": oid,
                "event_type": "PROPOSAL_DELIVERED",
                "old_status": "OPEN",
                "new_status": "PROPOSAL",
                "occurred_at": prop_time.isoformat(),
                "event_payload": {"proposal_version": "v1"},
                "run_id": None,
            })

            if status in ("WON", "LOST", "CANCELLED"):
                evt3_id = id_gen.opportunity_event_id()
                opportunity_events.append({
                    "opportunity_event_id": evt3_id,
                    "opportunity_id": oid,
                    "event_type": f"STAGE_{status}",
                    "old_status": "PROPOSAL",
                    "new_status": status,
                    "occurred_at": closed_at,
                    "event_payload": {"final_value": float(actual_val) if actual_val else 0.0},
                    "run_id": None,
                })

    opportunities.sort(key=lambda o: (o["created_at"], o["opportunity_id"]))
    opportunity_events.sort(key=lambda e: (e["occurred_at"], e["opportunity_event_id"]))
    return opportunities, opportunity_events

