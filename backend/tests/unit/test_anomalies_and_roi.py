"""Unit tests for Anomaly Injection, Exception Detection, and Campaign ROI calculations."""

from decimal import Decimal
import pytest

from src.attribution.config import load_config
from src.attribution.generator.anomalies import inject_anomalies_and_build_ground_truth
from src.attribution.generator.orchestrator import generate_dataset
from src.attribution.ids import DeterministicIDGenerator
from src.attribution.pipeline.attribution import AttributionEngine
from src.attribution.pipeline.exceptions import ExceptionDetector
from src.attribution.pipeline.metrics import evaluate_exception_detection
from src.attribution.pipeline.reconciliation import FinancialReconciler


@pytest.fixture
def test_setup():
    config = load_config("config/starter.yaml")
    id_gen = DeterministicIDGenerator(year=2026)
    dataset = generate_dataset(config)
    dataset, ground_truth = inject_anomalies_and_build_ground_truth(dataset, id_gen, config)
    return config, dataset, ground_truth


def test_anomaly_injection_five_scenarios(test_setup):
    _, _, ground_truth = test_setup
    assert len(ground_truth) == 5
    injected_types = {gt.issue_type for gt in ground_truth}
    expected_types = {
        "DUPLICATE_REVENUE",
        "POST_CONVERSION_TOUCH",
        "CURRENCY_MISMATCH",
        "MISSING_CAMPAIGN_COST",
        "UNSUPPORTED_IDENTITY_LINK",
    }
    assert injected_types == expected_types


def test_exception_detector_perfect_metrics(test_setup):
    config, dataset, ground_truth = test_setup
    detector = ExceptionDetector(run_id="RUN-TEST")
    detected = detector.detect_all(
        orders=dataset.orders,
        touchpoints=dataset.touchpoints,
        cost_records=dataset.cost_records,
        campaigns=dataset.campaigns,
        web_sessions=dataset.web_sessions,
        reporting_currency=config.reporting_currency,
    )

    metrics = evaluate_exception_detection(detected, ground_truth)
    assert metrics.true_positives == 5
    assert metrics.false_positives == 0
    assert metrics.false_negatives == 0
    assert metrics.precision == 1.0
    assert metrics.recall == 1.0
    assert metrics.f1_score == 1.0


def test_financial_reconciliation_and_roi(test_setup):
    config, dataset, ground_truth = test_setup
    engine = AttributionEngine(run_id="RUN-TEST")
    attr_exec = engine.compute_attribution(dataset.orders, dataset.touchpoints)

    detector = ExceptionDetector(run_id="RUN-TEST")
    detected = detector.detect_all(
        orders=dataset.orders,
        touchpoints=dataset.touchpoints,
        cost_records=dataset.cost_records,
        campaigns=dataset.campaigns,
        web_sessions=dataset.web_sessions,
        reporting_currency=config.reporting_currency,
    )
    issue_entities = {i.entity_id for i in detected}

    reconciler = FinancialReconciler(reporting_currency=config.reporting_currency)
    performances = reconciler.calculate_campaign_performance(
        campaigns=dataset.campaigns,
        cost_records=dataset.cost_records,
        attribution_results=attr_exec.attribution_results,
        detected_issue_entities=issue_entities,
    )

    assert len(performances) == len(dataset.campaigns)

    statuses = {p.cost_status for p in performances}
    assert "COMPLETE" in statuses
    # The injected missing cost campaign must be marked incomplete
    assert "INCOMPLETE_COST" in statuses

    for p in performances:
        if p.cost_status == "COMPLETE":
            assert p.actual_cost > 0
            if p.linear_roi is not None:
                # ROI formula: ((linear_rev - actual_cost) / actual_cost) * 100
                expected_roi = round(((p.linear_revenue - p.actual_cost) / p.actual_cost) * 100, 2)
                assert abs(p.linear_roi - expected_roi) < 0.05
        else:
            # ROI must be None (N/A) for incomplete or unresolved costs
            assert p.linear_roi is None

