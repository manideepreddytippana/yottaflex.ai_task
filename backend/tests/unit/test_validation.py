"""Unit tests for the validation engine and invariants."""

from pathlib import Path
import pytest

from src.attribution.pipeline.validate import DataValidator


@pytest.fixture
def test_data_dir():
    p = Path("data/generated/full") if Path("data/generated/full").is_dir() else Path("data/generated/starter")
    if not p.is_dir() or not (p / "campaign.csv").is_file():
        pytest.skip("Pipeline data not generated yet")
    return p


def test_validation_engine_all_pass_on_clean_data(test_data_dir):
    validator = DataValidator(test_data_dir)
    report = validator.execute_all()

    assert report.overall_status == "PASS"
    assert report.failed_checks == 0
    assert report.total_checks >= 35

    # Check key categories are present
    check_names = {f.check_name for f in report.findings}
    assert "pk_uniqueness_campaign" in check_names
    assert "fk_campaign_channel" in check_names
    assert "temporal_campaign_dates" in check_names
    assert "financial_order_net_revenue" in check_names
    assert "lifecycle_opp_event_consistency" in check_names

