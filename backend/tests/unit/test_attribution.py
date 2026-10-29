"""Unit tests for journey reconstruction, eligibility filtering, and attribution models."""

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
import pytest

from src.attribution.config import load_config
from src.attribution.generator.orchestrator import generate_dataset
from src.attribution.pipeline.attribution import AttributionEngine, reconcile_attribution
from src.attribution.pipeline.journeys import (
    filter_eligible_touchpoints_for_order,
    reconstruct_contact_journey,
)


def test_filter_eligible_touchpoints():
    order = {
        "order_id": "ORD-2026-000001",
        "contact_id": "CON-000001",
        "ordered_at": "2026-06-01T12:00:00+00:00",
        "net_revenue": 1000.00,
        "status": "PAID",
    }

    touches = [
        # 1. Valid touch within window
        {
            "touchpoint_id": "TOUCH-CON-000001-000001",
            "campaign_id": "CMP-2026-000001",
            "occurred_at": "2026-05-01T10:00:00+00:00",
            "identity_evidence": "AUTHENTICATED",
        },
        # 2. Touch older than 180 days lookback
        {
            "touchpoint_id": "TOUCH-CON-000001-000002",
            "campaign_id": "CMP-2026-000001",
            "occurred_at": "2025-10-01T10:00:00+00:00",
            "identity_evidence": "AUTHENTICATED",
        },
        # 3. Post-conversion touch
        {
            "touchpoint_id": "TOUCH-CON-000001-000003",
            "campaign_id": "CMP-2026-000002",
            "occurred_at": "2026-06-02T10:00:00+00:00",
            "identity_evidence": "AUTHENTICATED",
        },
        # 4. Touch with unsupported identity evidence
        {
            "touchpoint_id": "TOUCH-CON-000001-000004",
            "campaign_id": "CMP-2026-000003",
            "occurred_at": "2026-05-15T10:00:00+00:00",
            "identity_evidence": "NONE",
        },
    ]

    eligible, ineligible = filter_eligible_touchpoints_for_order(order, touches, lookback_window_days=180)

    assert len(eligible) == 1
    assert eligible[0]["touchpoint_id"] == "TOUCH-CON-000001-000001"

    assert len(ineligible) == 3
    reasons = {t["ineligibility_reason"] for t in ineligible}
    assert "OUTSIDE_LOOKBACK_WINDOW" in reasons
    assert "POST_CONVERSION" in reasons
    assert "UNSUPPORTED_IDENTITY_EVIDENCE" in reasons


def test_first_touch_and_last_touch_attribution():
    engine = AttributionEngine(run_id="RUN-TEST")
    order = {
        "order_id": "ORD-2026-000001",
        "contact_id": "CON-000001",
        "ordered_at": "2026-06-01T12:00:00+00:00",
        "net_revenue": 1000.00,
        "status": "PAID",
    }
    touches = [
        {
            "touchpoint_id": "TOUCH-CON-000001-000001",
            "contact_id": "CON-000001",
            "campaign_id": "CMP-2026-000001",
            "occurred_at": "2026-04-01T10:00:00+00:00",
            "identity_evidence": "AUTHENTICATED",
        },
        {
            "touchpoint_id": "TOUCH-CON-000001-000002",
            "contact_id": "CON-000001",
            "campaign_id": "CMP-2026-000002",
            "occurred_at": "2026-05-20T10:00:00+00:00",
            "identity_evidence": "AUTHENTICATED",
        },
    ]

    exec_result = engine.compute_attribution(
        orders=[order],
        touchpoints=touches,
        models=("FIRST_TOUCH", "LAST_TOUCH"),
    )

    results = exec_result.attribution_results
    assert len(results) == 2

    first_touch = next(r for r in results if r["model_name"] == "FIRST_TOUCH")
    last_touch = next(r for r in results if r["model_name"] == "LAST_TOUCH")

    assert first_touch["campaign_id"] == "CMP-2026-000001"
    assert first_touch["attributed_revenue"] == 1000.00
    assert first_touch["credit_share"] == 1.0

    assert last_touch["campaign_id"] == "CMP-2026-000002"
    assert last_touch["attributed_revenue"] == 1000.00
    assert last_touch["credit_share"] == 1.0


def test_linear_attribution_cent_allocation():
    engine = AttributionEngine(run_id="RUN-TEST")
    # 100.00 split across 3 distinct campaigns
    order = {
        "order_id": "ORD-2026-000001",
        "contact_id": "CON-000001",
        "ordered_at": "2026-06-01T12:00:00+00:00",
        "net_revenue": 100.00,
        "status": "PAID",
    }
    touches = [
        {
            "touchpoint_id": "TOUCH-CON-000001-000001",
            "contact_id": "CON-000001",
            "campaign_id": "CMP-2026-000001",
            "occurred_at": "2026-04-01T10:00:00+00:00",
            "identity_evidence": "AUTHENTICATED",
        },
        {
            "touchpoint_id": "TOUCH-CON-000001-000002",
            "contact_id": "CON-000001",
            "campaign_id": "CMP-2026-000002",
            "occurred_at": "2026-04-15T10:00:00+00:00",
            "identity_evidence": "AUTHENTICATED",
        },
        {
            "touchpoint_id": "TOUCH-CON-000001-000003",
            "contact_id": "CON-000001",
            "campaign_id": "CMP-2026-000003",
            "occurred_at": "2026-05-01T10:00:00+00:00",
            "identity_evidence": "AUTHENTICATED",
        },
    ]

    exec_result = engine.compute_attribution(
        orders=[order],
        touchpoints=touches,
        models=("LINEAR",),
    )

    results = exec_result.attribution_results
    assert len(results) == 3

    # Total must equal 100.00 exactly
    total_attributed = sum(r["attributed_revenue"] for r in results)
    assert round(total_attributed, 2) == 100.00

    # Remainder 1 cent should be allocated to earliest campaign (CMP-1)
    rev_by_cmp = {r["campaign_id"]: r["attributed_revenue"] for r in results}
    assert rev_by_cmp["CMP-2026-000001"] == 33.34
    assert rev_by_cmp["CMP-2026-000002"] == 33.33
    assert rev_by_cmp["CMP-2026-000003"] == 33.33


def test_reconciliation_pass_rate_on_generated_dataset():
    config = load_config("config/starter.yaml")
    dataset = generate_dataset(config)

    engine = AttributionEngine(lookback_window_days=config.conversion_window_days)
    exec_res = engine.compute_attribution(dataset.orders, dataset.touchpoints)

    for model in ("FIRST_TOUCH", "LAST_TOUCH", "LINEAR"):
        recon = reconcile_attribution(dataset.orders, exec_res.attribution_results, model_name=model)
        assert recon.status == "PASS"
        assert recon.orders_failed == 0
        assert recon.revenue_difference == Decimal("0.00")
        assert recon.orders_checked > 0

