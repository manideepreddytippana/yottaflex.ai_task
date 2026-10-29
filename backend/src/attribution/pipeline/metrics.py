"""Evaluation metrics module for exception detection and pipeline performance."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from src.attribution.generator.anomalies import GroundTruthRecord
from src.attribution.pipeline.exceptions import DetectedIssue
from src.attribution.pipeline.reconciliation import CampaignPerformanceRow


@dataclass
class ExceptionEvaluationMetrics:
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float
    per_issue_breakdown: dict[str, dict[str, int]]


@dataclass
class PipelineEvaluationSummary:
    exception_metrics: ExceptionEvaluationMetrics
    attribution_coverage_rate: float
    roi_availability_rate: float
    reconciliation_pass_rate: float
    total_campaigns: int
    total_orders_evaluated: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_exception_detection(
    detected_issues: list[DetectedIssue],
    ground_truth: list[GroundTruthRecord],
) -> ExceptionEvaluationMetrics:
    """Evaluate detector findings against ground-truth fixtures."""
    # Match on (entity_type, entity_id, issue_type)
    gt_set = {(gt.entity_type, gt.entity_id, gt.issue_type) for gt in ground_truth}
    det_set = {(di.entity_type, di.entity_id, di.issue_type) for di in detected_issues}

    tp_set = gt_set.intersection(det_set)
    fp_set = det_set - gt_set
    fn_set = gt_set - det_set

    tp = len(tp_set)
    fp = len(fp_set)
    fn = len(fn_set)

    precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 1.0
    recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 1.0
    f1 = round((2 * precision * recall) / (precision + recall), 4) if (precision + recall) > 0 else 1.0

    # Breakdown per issue type
    breakdown: dict[str, dict[str, int]] = {}
    all_issues = {gt.issue_type for gt in ground_truth}.union({di.issue_type for di in detected_issues})
    for it in all_issues:
        it_gt = {item for item in gt_set if item[2] == it}
        it_det = {item for item in det_set if item[2] == it}
        it_tp = len(it_gt.intersection(it_det))
        it_fp = len(it_det - it_gt)
        it_fn = len(it_gt - it_det)
        breakdown[it] = {"TP": it_tp, "FP": it_fp, "FN": it_fn}

    return ExceptionEvaluationMetrics(
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        precision=precision,
        recall=recall,
        f1_score=f1,
        per_issue_breakdown=breakdown,
    )


def compute_pipeline_metrics(
    detected_issues: list[DetectedIssue],
    ground_truth: list[GroundTruthRecord],
    campaign_performances: list[CampaignPerformanceRow],
    orders: list[dict[str, Any]],
    attribution_results: list[dict[str, Any]],
    reconciliation_passed: bool,
) -> PipelineEvaluationSummary:
    """Compute overall evaluation metrics covering exceptions, attribution coverage, and ROI availability."""
    exc_metrics = evaluate_exception_detection(detected_issues, ground_truth)

    # Attribution coverage: paid orders with attributed revenue > 0
    paid_orders = [o for o in orders if o.get("status") == "PAID"]
    attributed_order_ids = {r["order_id"] for r in attribution_results if r.get("attributed_revenue", 0) > 0}
    coverage = round(len(attributed_order_ids) / len(paid_orders), 4) if paid_orders else 1.0

    # ROI availability rate: campaigns with complete cost status
    total_cmps = len(campaign_performances)
    complete_cmps = sum(1 for c in campaign_performances if c.cost_status == "COMPLETE")
    roi_avail = round(complete_cmps / total_cmps, 4) if total_cmps > 0 else 1.0

    recon_rate = 1.0 if reconciliation_passed else 0.0

    return PipelineEvaluationSummary(
        exception_metrics=exc_metrics,
        attribution_coverage_rate=coverage,
        roi_availability_rate=roi_avail,
        reconciliation_pass_rate=recon_rate,
        total_campaigns=total_cmps,
        total_orders_evaluated=len(paid_orders),
    )

