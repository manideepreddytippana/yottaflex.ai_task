"""Deterministic generation of Campaign Cost Records and Exchange Rates."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
import random
from typing import Any

from src.attribution.ids import DeterministicIDGenerator


# Fixed exchange rates relative to INR (reporting currency)
EXCHANGE_RATES_TO_INR: dict[str, Decimal] = {
    "INR": Decimal("1.00000000"),
    "USD": Decimal("83.50000000"),
    "AUD": Decimal("54.25000000"),
    "EUR": Decimal("90.10000000"),
    "GBP": Decimal("105.80000000"),
}

COST_TYPES = ["MEDIA", "AGENCY", "PRODUCTION", "PLATFORM", "OTHER"]


def generate_cost_records(
    campaigns: list[dict[str, Any]],
    id_gen: DeterministicIDGenerator,
    rng: random.Random,
    reporting_currency: str = "INR",
) -> list[dict[str, Any]]:
    """Generate cost records across active campaign intervals with currency normalization."""
    cost_records: list[dict[str, Any]] = []

    for campaign in campaigns:
        cmp_id = campaign["campaign_id"]
        cmp_curr = campaign["currency"]
        budget = Decimal(str(campaign["budget_amount"]))
        start_at = datetime.fromisoformat(campaign["start_at"])
        end_at = datetime.fromisoformat(campaign["end_at"])

        duration_days = max(7, (end_at - start_at).days)
        # Periodic spend entries: every 7 to 14 days
        interval_days = rng.randint(7, 14)
        num_entries = max(2, duration_days // interval_days)

        # Total spend around 70% - 95% of planned budget
        spend_ratio = Decimal(str(rng.uniform(0.70, 0.95))).quantize(Decimal("0.01"))
        target_total_spend = (budget * spend_ratio).quantize(Decimal("0.01"))
        base_slice = (target_total_spend / Decimal(str(num_entries))).quantize(Decimal("0.01"))

        current_date = start_at
        allocated_so_far = Decimal("0.00")

        fx_rate = EXCHANGE_RATES_TO_INR.get(cmp_curr, Decimal("1.00000000"))

        for entry_idx in range(num_entries):
            cid = id_gen.cost_id()
            incurred_at = current_date + timedelta(days=rng.randint(1, interval_days))
            if incurred_at > end_at:
                incurred_at = end_at

            if entry_idx == num_entries - 1:
                amount = target_total_spend - allocated_so_far
            else:
                variation = Decimal(str(rng.uniform(0.85, 1.15))).quantize(Decimal("0.01"))
                amount = (base_slice * variation).quantize(Decimal("0.01"))
                allocated_so_far += amount

            # Converted reporting amount
            reporting_amt = (amount * fx_rate).quantize(Decimal("0.01"))
            cost_type = rng.choice(COST_TYPES)
            rate_date = incurred_at.date().isoformat()

            cost_records.append({
                "cost_record_id": cid,
                "campaign_id": cmp_id,
                "incurred_at": incurred_at.isoformat(),
                "cost_type": cost_type,
                "amount": float(amount),
                "currency": cmp_curr,
                "exchange_rate_to_reporting": float(fx_rate),
                "reporting_amount": float(reporting_amt),
                "rate_date": rate_date,
                "source_reference": f"INV-{cid.replace('COST-', '')}",
                "issue_type": None,
            })

            current_date += timedelta(days=interval_days)

    cost_records.sort(key=lambda c: (c["incurred_at"], c["cost_record_id"]))
    return cost_records

