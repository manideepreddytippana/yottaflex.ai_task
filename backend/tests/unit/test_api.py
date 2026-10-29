"""Unit tests for the Attribution REST API route handlers and schemas."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
import pytest
from fastapi import HTTPException

from src.attribution.api.routes.attribution import compare_attribution, get_order_attribution
from src.attribution.api.routes.campaigns import get_campaign_detail, get_campaign_roi, list_campaigns
from src.attribution.api.routes.contacts import get_customer_journey
from src.attribution.api.routes.exports import list_exports
from src.attribution.api.routes.health import get_health
from src.attribution.api.routes.issues import get_issue_detail, list_issues
from src.attribution.api.routes.metrics import get_metrics
from src.attribution.api.routes.runs import get_run, get_validation_summary, list_runs, trigger_run
from src.attribution.api.schemas import (
    AttributionComparisonResponse,
    CampaignDetailResponse,
    CampaignListResponse,
    CampaignROIResponse,
    CustomerJourneyResponse,
    DataIssueDetailResponse,
    DataIssueListResponse,
    EvaluationMetricsResponse,
    HealthResponse,
    OrderAttributionResponse,
    RunCreateRequest,
    RunDetailResponse,
    RunExportsResponse,
    RunSummary,
    ValidationSummaryResponse,
)
from pathlib import Path

DATA_DIR = Path("data/generated/full") if Path("data/generated/full").is_dir() else Path("data/generated/starter")


@pytest.fixture(autouse=True)
def check_data_prerequisites(request):
    """Skip data-dependent API tests if pipeline data has not been generated and loaded yet."""
    if request.node.name == "test_health_endpoint":
        return
    if not DATA_DIR.is_dir() or not (DATA_DIR / "attribution_result.csv").is_file():
        pytest.skip("API integration tests require generated dataset. Run 'python scripts/run_pipeline.py' first.")


def test_health_endpoint():
    res = get_health()
    assert isinstance(res, HealthResponse)
    assert res.status == "healthy"
    assert res.version == "1.0.0"
    assert res.database_connected is True


def test_list_runs():
    runs = list_runs()
    assert isinstance(runs, list)
    assert len(runs) >= 1
    assert isinstance(runs[0], RunSummary)
    assert runs[0].dataset_scale in ("starter", "full")


def test_trigger_run():
    req = RunCreateRequest(scale="starter", seed=20261022)
    res = trigger_run(req)
    assert isinstance(res, RunSummary)
    assert res.run_id.startswith("RUN-20261022-")


def test_get_run_detail():
    runs = list_runs()
    run_id = runs[0].run_id
    res = get_run(run_id)
    assert isinstance(res, RunDetailResponse)
    assert res.run_id == run_id
    assert res.row_counts.get("campaign") in (25, 500)
    assert "checksums" in res.__dict__


def test_get_run_not_found():
    with pytest.raises(HTTPException) as exc_info:
        get_run("NON-EXISTENT-RUN-999")
    assert exc_info.value.status_code == 404


def test_get_run_validation():
    runs = list_runs()
    run_id = runs[0].run_id
    res = get_validation_summary(run_id)
    assert isinstance(res, ValidationSummaryResponse)
    assert res.overall_status == "PASS"
    assert res.total_checks >= 35
    assert res.failed_checks == 0


def test_list_campaigns():
    res = list_campaigns(page=1, page_size=10)
    assert isinstance(res, CampaignListResponse)
    assert res.total in (25, 500)
    assert len(res.campaigns) == 10
    c1 = res.campaigns[0]
    assert c1.actual_spend >= Decimal("0.00")
    assert c1.attributed_revenue_linear >= Decimal("0.00")
    assert c1.spend_coverage_status in ("COMPLETE", "INCOMPLETE")


def test_filter_campaigns():
    res = list_campaigns(search="Spring")
    assert isinstance(res, CampaignListResponse)
    assert isinstance(res.campaigns, list)


def test_get_campaign_detail():
    res = get_campaign_detail("CMP-2026-000001")
    assert isinstance(res, CampaignDetailResponse)
    assert res.campaign_id == "CMP-2026-000001"
    assert len(res.creatives) > 0
    assert len(res.audiences) > 0
    assert res.first_touch_revenue >= Decimal("0.00")
    assert res.linear_revenue >= Decimal("0.00")


def test_get_campaign_roi():
    res = get_campaign_roi("CMP-2026-000001")
    assert isinstance(res, CampaignROIResponse)
    assert res.campaign_id == "CMP-2026-000001"
    assert "first_touch" in res.__dict__
    assert "last_touch" in res.__dict__
    assert "linear" in res.__dict__
    assert res.reconciliation_status == "PASS"


def test_compare_attribution():
    res = compare_attribution()
    assert isinstance(res, AttributionComparisonResponse)
    assert res.reporting_currency == "INR"
    assert len(res.models) == 3
    model_names = [m.model for m in res.models]
    assert "FIRST_TOUCH" in model_names
    assert "LAST_TOUCH" in model_names
    assert "LINEAR" in model_names
    for m in res.models:
        assert m.reconciliation_status == "PASS"
        assert m.attributed_revenue > Decimal("0.00")
    assert len(res.campaign_comparison) in (25, 500)


def test_order_attribution():
    res = get_order_attribution("ORD-2026-000001")
    assert isinstance(res, OrderAttributionResponse)
    assert res.order_id == "ORD-2026-000001"
    assert "LINEAR" in res.models
    assert len(res.models["LINEAR"]) > 0
    assert len(res.models["LINEAR"][0].touchpoints) > 0


def test_customer_journey():
    res = get_customer_journey("CON-000001")
    assert isinstance(res, CustomerJourneyResponse)
    assert res.contact_id == "CON-000001"
    assert len(res.timeline) > 0
    occurred_times = [item.occurred_at for item in res.timeline]
    assert occurred_times == sorted(occurred_times)


def test_list_issues():
    res = list_issues()
    assert isinstance(res, DataIssueListResponse)
    assert res.total == 5
    assert len(res.issues) == 5
    issue_types = [i.issue_type for i in res.issues]
    assert "MISSING_CAMPAIGN_COST" in issue_types
    assert "POST_CONVERSION_TOUCH" in issue_types


def test_get_issue_detail():
    res = get_issue_detail("ISSUE-000001")
    assert isinstance(res, DataIssueDetailResponse)
    assert res.issue_id == "ISSUE-000001"
    assert isinstance(res.related_records, list)


def test_get_metrics():
    res = get_metrics()
    assert isinstance(res, EvaluationMetricsResponse)
    assert res.precision == 1.0
    assert res.recall == 1.0
    assert res.f1_score == 1.0
    assert res.reconciliation_pass_rate_percent == 100.0


def test_get_exports():
    runs = list_runs()
    run_id = runs[0].run_id
    res = list_exports(run_id)
    assert isinstance(res, RunExportsResponse)
    assert res.run_id == run_id
    assert len(res.exports) > 10
    filenames = [e.filename for e in res.exports]
    assert "seed.sql" in filenames
    assert "manifest.json" in filenames
    assert "checksums.sha256" in filenames
