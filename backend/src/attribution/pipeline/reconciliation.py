"""Financial reconciliation and Campaign ROI computation engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Any


@dataclass
class CampaignPerformanceRow:
    campaign_id: str
    name: str
    channel_id: str
    budget_amount: float
    actual_cost: float
    cost_status: str  # COMPLETE, INCOMPLETE_COST, CURRENCY_UNRESOLVED, ZERO_COST
    first_touch_revenue: float
    first_touch_roi: float | None
    last_touch_revenue: float
    last_touch_roi: float | None
    linear_revenue: float
    linear_roi: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class FinancialReconciler:
    """Computes normalized campaign costs, deduplicated revenues, and multi-model ROI."""

    def __init__(self, reporting_currency: str = "INR") -> None:
        self.reporting_currency = reporting_currency

    def calculate_campaign_performance(
        self,
        campaigns: list[dict[str, Any]],
        cost_records: list[dict[str, Any]],
        attribution_results: list[dict[str, Any]],
        detected_issue_entities: set[str] | None = None,
    ) -> list[CampaignPerformanceRow]:
        """Calculate spend, attributed revenues, and ROI per campaign across all models."""
        if detected_issue_entities is None:
            detected_issue_entities = set()

        # Aggregate costs per campaign
        campaign_costs: dict[str, Decimal] = {}
        campaign_cost_status: dict[str, str] = {}

        for cmp in campaigns:
            cid = cmp["campaign_id"]
            cmp_records = [c for c in cost_records if c["campaign_id"] == cid]

            if not cmp_records:
                campaign_costs[cid] = Decimal("0.00")
                campaign_cost_status[cid] = "INCOMPLETE_COST"
                continue

            # Check if any cost record has unresolved currency
            has_currency_mismatch = any(
                c["cost_record_id"] in detected_issue_entities
                or c.get("exchange_rate_to_reporting") is None
                or c.get("reporting_amount") is None
                for c in cmp_records
            )

            if has_currency_mismatch:
                campaign_costs[cid] = Decimal("0.00")
                campaign_cost_status[cid] = "CURRENCY_UNRESOLVED"
                continue

            total_cost = sum(
                (Decimal(str(c["reporting_amount"])) for c in cmp_records),
                Decimal("0.00"),
            ).quantize(Decimal("0.01"))

            campaign_costs[cid] = total_cost
            if total_cost == Decimal("0.00"):
                campaign_cost_status[cid] = "ZERO_COST"
            else:
                campaign_cost_status[cid] = "COMPLETE"

        # Aggregate attributed revenue per (campaign_id, model_name)
        attr_revenue: dict[tuple[str, str], Decimal] = {}
        for r in attribution_results:
            cid = r.get("campaign_id")
            if not cid:
                continue
            model = r["model_name"]
            rev = Decimal(str(r["attributed_revenue"]))
            key = (cid, model)
            attr_revenue[key] = attr_revenue.get(key, Decimal("0.00")) + rev

        rows: list[CampaignPerformanceRow] = []

        for cmp in campaigns:
            cid = cmp["campaign_id"]
            cost = campaign_costs[cid]
            status = campaign_cost_status[cid]

            ft_rev = attr_revenue.get((cid, "FIRST_TOUCH"), Decimal("0.00")).quantize(Decimal("0.01"))
            lt_rev = attr_revenue.get((cid, "LAST_TOUCH"), Decimal("0.00")).quantize(Decimal("0.01"))
            lin_rev = attr_revenue.get((cid, "LINEAR"), Decimal("0.00")).quantize(Decimal("0.01"))

            # Calculate ROI if cost is valid and positive
            ft_roi = self._compute_roi(ft_rev, cost, status)
            lt_roi = self._compute_roi(lt_rev, cost, status)
            lin_roi = self._compute_roi(lin_rev, cost, status)

            rows.append(
                CampaignPerformanceRow(
                    campaign_id=cid,
                    name=cmp["name"],
                    channel_id=cmp["channel_id"],
                    budget_amount=float(cmp["budget_amount"]),
                    actual_cost=float(cost),
                    cost_status=status,
                    first_touch_revenue=float(ft_rev),
                    first_touch_roi=ft_roi,
                    last_touch_revenue=float(lt_rev),
                    last_touch_roi=lt_roi,
                    linear_revenue=float(lin_rev),
                    linear_roi=lin_roi,
                )
            )

        rows.sort(key=lambda x: x.campaign_id)
        return rows

    def _compute_roi(self, revenue: Decimal, cost: Decimal, status: str) -> float | None:
        """Calculate ROI percentage: ((Revenue - Cost) / Cost) * 100."""
        if status != "COMPLETE" or cost <= Decimal("0.00"):
            return None
        roi_dec = ((revenue - cost) / cost * Decimal("100")).quantize(Decimal("0.01"))
        return float(roi_dec)

