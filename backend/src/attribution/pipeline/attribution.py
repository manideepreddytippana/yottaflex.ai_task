"""Multi-model attribution computation engine and financial reconciliation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from src.attribution.pipeline.journeys import filter_eligible_touchpoints_for_order


MODEL_VERSION = "v1.0"


@dataclass
class AttributionExecutionResult:
    attribution_results: list[dict[str, Any]]
    attribution_touchpoints: list[dict[str, Any]]


@dataclass
class OrderReconciliationResult:
    order_id: str
    model_name: str
    order_net_revenue: Decimal
    total_attributed_revenue: Decimal
    total_credit_share: Decimal
    revenue_diff: Decimal
    share_diff: Decimal
    is_duplicate: bool
    status: str  # PASS / FAIL


@dataclass
class ReconciliationSummary:
    model_name: str
    orders_checked: int
    orders_passed: int
    orders_failed: int
    total_order_revenue: Decimal
    total_attributed_revenue: Decimal
    revenue_difference: Decimal
    status: str  # PASS / FAIL
    details: list[OrderReconciliationResult]


class AttributionEngine:
    """Computes First-Touch, Last-Touch, and Linear Attribution models with cent-perfect reconciliation."""

    def __init__(
        self,
        lookback_window_days: int = 180,
        run_id: str = "RUN-DEFAULT",
    ) -> None:
        self.lookback_window_days = lookback_window_days
        self.run_id = run_id
        self.model_version = MODEL_VERSION

    def compute_attribution(
        self,
        orders: list[dict[str, Any]],
        touchpoints: list[dict[str, Any]],
        models: tuple[str, ...] = ("FIRST_TOUCH", "LAST_TOUCH", "LINEAR"),
        calculated_at: str = "2026-10-31T23:59:59+00:00",
    ) -> AttributionExecutionResult:
        """Run attribution models across all orders and return results and touchpoint bridges."""
        touches_by_contact: dict[str, list[dict[str, Any]]] = {}
        for t in touchpoints:
            cid = t.get("contact_id")
            if cid:
                touches_by_contact.setdefault(cid, []).append(t)

        all_results: list[dict[str, Any]] = []
        all_touchpoint_bridges: list[dict[str, Any]] = []
        now_iso = calculated_at

        # Sort orders deterministically by ordered_at, order_id
        sorted_orders = sorted(
            [o for o in orders if o.get("status") == "PAID" and Decimal(str(o.get("net_revenue", 0))) > 0],
            key=lambda x: (x["ordered_at"], x["order_id"]),
        )

        seen_txn_keys: set[str] = set()

        for order in sorted_orders:
            order_id = order["order_id"]
            contact_id = order["contact_id"]
            txn_key = order.get("economic_transaction_key", order_id)
            net_revenue = Decimal(str(order["net_revenue"])).quantize(Decimal("0.01"))

            # Deduplication policy: If economic_transaction_key was already attributed, do not double-count
            if txn_key in seen_txn_keys:
                for model_name in models:
                    res_id = f"ATTR-{order_id}-{model_name}-DUP"
                    all_results.append({
                        "attribution_result_id": res_id,
                        "order_id": order_id,
                        "campaign_id": None,
                        "model_name": model_name,
                        "model_version": self.model_version,
                        "credit_share": float(Decimal("0.000000")),
                        "attributed_revenue": float(Decimal("0.00")),
                        "calculated_at": now_iso,
                        "decision_reason": f"DUPLICATE_REVENUE: Key {txn_key} already counted; revenue attributed once",
                        "run_id": self.run_id,
                        "issue_type": "DUPLICATE_REVENUE",
                    })
                continue

            seen_txn_keys.add(txn_key)

            contact_touches = touches_by_contact.get(contact_id, [])
            eligible_touches, _ = filter_eligible_touchpoints_for_order(
                order=order,
                contact_touchpoints=contact_touches,
                lookback_window_days=self.lookback_window_days,
            )

            for model_name in models:
                res, bridges = self._attribute_single_order(
                    order_id=order_id,
                    net_revenue=net_revenue,
                    eligible_touches=eligible_touches,
                    model_name=model_name,
                    calculated_at=now_iso,
                )
                all_results.extend(res)
                all_touchpoint_bridges.extend(bridges)

        return AttributionExecutionResult(
            attribution_results=all_results,
            attribution_touchpoints=all_touchpoint_bridges,
        )

    def _attribute_single_order(
        self,
        order_id: str,
        net_revenue: Decimal,
        eligible_touches: list[dict[str, Any]],
        model_name: str,
        calculated_at: str,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Compute attribution for a single non-duplicate order and model."""
        if not eligible_touches:
            res_id = f"ATTR-{order_id}-{model_name}-UNATTR"
            result_row = {
                "attribution_result_id": res_id,
                "order_id": order_id,
                "campaign_id": None,
                "model_name": model_name,
                "model_version": self.model_version,
                "credit_share": float(Decimal("1.000000")),
                "attributed_revenue": float(net_revenue),
                "calculated_at": calculated_at,
                "decision_reason": "No eligible touchpoints found within lookback window",
                "run_id": self.run_id,
                "issue_type": None,
            }
            return [result_row], []

        if model_name == "FIRST_TOUCH":
            chosen_touch = eligible_touches[0]
            cmp_id = chosen_touch["campaign_id"]
            res_id = f"ATTR-{order_id}-FIRST_TOUCH-{cmp_id}"
            result_row = {
                "attribution_result_id": res_id,
                "order_id": order_id,
                "campaign_id": cmp_id,
                "model_name": "FIRST_TOUCH",
                "model_version": self.model_version,
                "credit_share": float(Decimal("1.000000")),
                "attributed_revenue": float(net_revenue),
                "calculated_at": calculated_at,
                "decision_reason": f"First touchpoint {chosen_touch['touchpoint_id']} received 100% credit",
                "run_id": self.run_id,
                "issue_type": None,
            }
            bridge = {
                "attribution_result_id": res_id,
                "touchpoint_id": chosen_touch["touchpoint_id"],
                "contribution_weight": float(Decimal("1.000000")),
            }
            return [result_row], [bridge]

        elif model_name == "LAST_TOUCH":
            chosen_touch = eligible_touches[-1]
            cmp_id = chosen_touch["campaign_id"]
            res_id = f"ATTR-{order_id}-LAST_TOUCH-{cmp_id}"
            result_row = {
                "attribution_result_id": res_id,
                "order_id": order_id,
                "campaign_id": cmp_id,
                "model_name": "LAST_TOUCH",
                "model_version": self.model_version,
                "credit_share": float(Decimal("1.000000")),
                "attributed_revenue": float(net_revenue),
                "calculated_at": calculated_at,
                "decision_reason": f"Last touchpoint {chosen_touch['touchpoint_id']} received 100% credit",
                "run_id": self.run_id,
                "issue_type": None,
            }
            bridge = {
                "attribution_result_id": res_id,
                "touchpoint_id": chosen_touch["touchpoint_id"],
                "contribution_weight": float(Decimal("1.000000")),
            }
            return [result_row], [bridge]

        elif model_name == "LINEAR":
            campaign_first_touch: dict[str, dict[str, Any]] = {}
            campaign_touches: dict[str, list[dict[str, Any]]] = {}
            for t in eligible_touches:
                cid = t["campaign_id"]
                if cid not in campaign_first_touch:
                    campaign_first_touch[cid] = t
                campaign_touches.setdefault(cid, []).append(t)

            distinct_campaigns = list(campaign_first_touch.keys())
            n = len(distinct_campaigns)

            share_per_campaign = (Decimal("1.0") / Decimal(str(n))).quantize(Decimal("0.000001"))

            total_cents = int(net_revenue * 100)
            base_cents = total_cents // n
            remainder_cents = total_cents % n

            results: list[dict[str, Any]] = []
            bridges: list[dict[str, Any]] = []

            for idx, cmp_id in enumerate(distinct_campaigns):
                cents = base_cents + (1 if idx < remainder_cents else 0)
                campaign_rev = (Decimal(cents) / Decimal("100")).quantize(Decimal("0.01"))

                res_id = f"ATTR-{order_id}-LINEAR-{cmp_id}"
                results.append({
                    "attribution_result_id": res_id,
                    "order_id": order_id,
                    "campaign_id": cmp_id,
                    "model_name": "LINEAR",
                    "model_version": self.model_version,
                    "credit_share": float(share_per_campaign),
                    "attributed_revenue": float(campaign_rev),
                    "calculated_at": calculated_at,
                    "decision_reason": f"Linear equal split across {n} campaigns with remainder cent allocation",
                    "run_id": self.run_id,
                    "issue_type": None,
                })

                c_touches = campaign_touches[cmp_id]
                t_weight = (Decimal("1.0") / Decimal(len(c_touches))).quantize(Decimal("0.000001"))
                for ct in c_touches:
                    bridges.append({
                        "attribution_result_id": res_id,
                        "touchpoint_id": ct["touchpoint_id"],
                        "contribution_weight": float(t_weight),
                    })

            return results, bridges

        raise ValueError(f"Unknown attribution model: {model_name}")


def reconcile_attribution(
    orders: list[dict[str, Any]],
    attribution_results: list[dict[str, Any]],
    model_name: str,
) -> ReconciliationSummary:
    """Verify that attribution results reconcile down to the cent for each order and globally."""
    results_by_order: dict[str, list[dict[str, Any]]] = {}
    for r in attribution_results:
        if r["model_name"] == model_name:
            results_by_order.setdefault(r["order_id"], []).append(r)

    # Sort orders chronologically
    sorted_orders = sorted(
        [o for o in orders if o.get("status") == "PAID" and Decimal(str(o.get("net_revenue", 0))) > 0],
        key=lambda x: (x["ordered_at"], x["order_id"]),
    )

    seen_keys = set()
    order_recons: list[OrderReconciliationResult] = []
    total_order_rev = Decimal("0.00")
    total_attr_rev = Decimal("0.00")

    passed_count = 0
    failed_count = 0

    for o in sorted_orders:
        oid = o["order_id"]
        txn_key = o.get("economic_transaction_key", oid)
        net_rev = Decimal(str(o["net_revenue"])).quantize(Decimal("0.01"))

        is_duplicate = txn_key in seen_keys
        if not is_duplicate:
            seen_keys.add(txn_key)
            total_order_rev += net_rev

        o_results = results_by_order.get(oid, [])
        attr_sum = sum((Decimal(str(r["attributed_revenue"])) for r in o_results), Decimal("0.00")).quantize(Decimal("0.01"))
        share_sum = sum((Decimal(str(r["credit_share"])) for r in o_results), Decimal("0.000000")).quantize(Decimal("0.000001"))

        if not is_duplicate:
            total_attr_rev += attr_sum
            rev_diff = abs(net_rev - attr_sum)
            share_diff = abs(Decimal("1.000000") - share_sum)
            is_pass = rev_diff == Decimal("0.00") and share_diff <= Decimal("0.00001")
        else:
            # Duplicate order must have 0 attributed revenue to prevent double-counting
            rev_diff = attr_sum
            share_diff = share_sum
            is_pass = attr_sum == Decimal("0.00") and share_sum == Decimal("0.000000")

        if is_pass:
            passed_count += 1
        else:
            failed_count += 1

        order_recons.append(
            OrderReconciliationResult(
                order_id=oid,
                model_name=model_name,
                order_net_revenue=net_rev,
                total_attributed_revenue=attr_sum,
                total_credit_share=share_sum,
                revenue_diff=rev_diff,
                share_diff=share_diff,
                is_duplicate=is_duplicate,
                status="PASS" if is_pass else "FAIL",
            )
        )

    global_diff = abs(total_order_rev - total_attr_rev)
    global_status = "PASS" if failed_count == 0 and global_diff == Decimal("0.00") else "FAIL"

    return ReconciliationSummary(
        model_name=model_name,
        orders_checked=len(sorted_orders),
        orders_passed=passed_count,
        orders_failed=failed_count,
        total_order_revenue=total_order_rev,
        total_attributed_revenue=total_attr_rev,
        revenue_difference=global_diff,
        status=global_status,
        details=order_recons,
    )
