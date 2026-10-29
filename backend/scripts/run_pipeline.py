"""End-to-End Pipeline Runner: Ingests data, executes attribution, reconciles ROI, and detects exceptions."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from decimal import Decimal
import json
from pathlib import Path
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.attribution.config import load_config
from src.attribution.export.csv_export import write_table_csv
from src.attribution.generator.anomalies import (
    GroundTruthRecord,
    export_ground_truth,
    inject_anomalies_and_build_ground_truth,
)
from src.attribution.generator.orchestrator import generate_dataset
from src.attribution.ids import DeterministicIDGenerator
from src.attribution.pipeline.attribution import AttributionEngine, reconcile_attribution
from src.attribution.pipeline.exceptions import ExceptionDetector
from src.attribution.pipeline.metrics import compute_pipeline_metrics
from src.attribution.pipeline.reconciliation import FinancialReconciler
from src.attribution.pipeline.validate import DataValidator


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Marketing Attribution & ROI Pipeline")
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default="config/starter.yaml",
        help="Path to YAML configuration file",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        default="data/generated/starter",
        help="Directory to read data from and export derived analytics",
    )
    args = parser.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.is_file():
        cfg_path = PROJECT_ROOT / args.config

    config = load_config(cfg_path)
    out_dir = Path(args.output_dir)
    if not out_dir.is_dir() and not out_dir.is_absolute():
        out_dir = PROJECT_ROOT / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    gt_dir = PROJECT_ROOT / "data" / "ground_truth"

    print(f"================================================================================")
    print(f"MARKETING CAMPAIGN ATTRIBUTION & ROI ANALYSIS PIPELINE")
    print(f"Seed: {config.seed} | Scale: {config.dataset_scale} | Currency: {config.reporting_currency}")
    print(f"================================================================================")

    # 1. Generate clean dataset
    print("\n[Step 1/6] Generating synthetic baseline dataset...")
    id_gen = DeterministicIDGenerator(year=2026)
    dataset = generate_dataset(config)

    # 2. Inject Anomaly Fixtures and Export Ground Truth
    print("[Step 2/6] Injecting 5 controlled anomalies and creating isolated ground truth...")
    dataset, ground_truth = inject_anomalies_and_build_ground_truth(dataset, id_gen, config)
    gt_path = gt_dir / "ground_truth.csv"
    export_ground_truth(ground_truth, gt_path)
    print(f"  -> {len(ground_truth)} ground truth cases written to {gt_path}")

    # Export all entities to output directory so validation and downstream read updated rows
    from src.attribution.export.csv_export import export_dataset_to_csv
    export_dataset_to_csv(dataset, out_dir)

    # 3. Structural & Temporal Validation
    print("\n[Step 3/6] Running data validation checks...")
    validator = DataValidator(out_dir)
    val_report = validator.execute_all()
    print(f"  -> Validation Status: {val_report.overall_status} ({val_report.passed_checks}/{val_report.total_checks} checks passed)")

    val_dict = val_report.to_dict()
    val_summary_path = out_dir / "validation_summary.json"
    with open(val_summary_path, "w", encoding="utf-8") as f:
        json.dump({
            "overall_status": val_report.overall_status,
            "total_checks": val_report.total_checks,
            "passed_checks": val_report.passed_checks,
            "failed_checks": val_report.failed_checks,
            "executed_at": val_report.executed_at,
            "checks": val_dict["findings"],
        }, f, indent=2)

    run_id = f"RUN-{config.seed}-{config.dataset_scale}"
    val_csv_rows = [
        {
            "validation_result_id": f"VAL-{i+1:05d}",
            "run_id": run_id,
            "check_name": f.check_name,
            "entity_name": f.entity_name,
            "records_checked": f.records_checked,
            "failure_count": f.failure_count,
            "status": f.status,
            "details_json": json.dumps(f.details),
            "executed_at": val_report.executed_at,
        }
        for i, f in enumerate(val_report.findings)
    ]
    write_table_csv(val_csv_rows, out_dir / "validation_result.csv")

    # 4. Attribution Engine
    print("\n[Step 4/6] Executing multi-model attribution engine (First-Touch, Last-Touch, Linear)...")
    engine = AttributionEngine(
        lookback_window_days=config.conversion_window_days,
        run_id=run_id,
    )
    attr_exec = engine.compute_attribution(
        orders=dataset.orders,
        touchpoints=dataset.touchpoints,
        models=("FIRST_TOUCH", "LAST_TOUCH", "LINEAR"),
    )
    print(f"  -> Generated {len(attr_exec.attribution_results)} attribution allocations across {len(dataset.orders)} orders")

    # Export attribution results and touchpoint bridges
    write_table_csv(attr_exec.attribution_results, out_dir / "attribution_result.csv")
    write_table_csv(attr_exec.attribution_touchpoints, out_dir / "attribution_touchpoint.csv")

    # Reconcile all models
    recon_summaries = {}
    recon_all_pass = True
    print("\nAttribution Financial Reconciliation Results:")
    for model in ("FIRST_TOUCH", "LAST_TOUCH", "LINEAR"):
        recon = reconcile_attribution(dataset.orders, attr_exec.attribution_results, model)
        recon_summaries[model] = {
            "status": recon.status,
            "orders_checked": recon.orders_checked,
            "orders_passed": recon.orders_passed,
            "orders_failed": recon.orders_failed,
            "total_order_revenue": float(recon.total_order_revenue),
            "total_attributed_revenue": float(recon.total_attributed_revenue),
            "difference": float(recon.revenue_difference),
        }
        if recon.status != "PASS":
            recon_all_pass = False
        print(f"  [{model:<11}] Status: {recon.status} | Orders Passed: {recon.orders_passed}/{recon.orders_checked} | Revenue Diff: {recon.revenue_difference} {config.reporting_currency}")

    # 5. Exception Detection Engine
    print("\n[Step 5/6] Executing exception detector on source records (without ground truth access)...")
    detector = ExceptionDetector(run_id=run_id)
    detected_issues = detector.detect_all(
        orders=dataset.orders,
        touchpoints=dataset.touchpoints,
        cost_records=dataset.cost_records,
        campaigns=dataset.campaigns,
        web_sessions=dataset.web_sessions,
        reporting_currency=config.reporting_currency,
    )
    print(f"  -> Detected {len(detected_issues)} data quality anomalies across 5 categories")
    detected_issue_dicts = [i.to_dict() for i in detected_issues]
    write_table_csv(detected_issue_dicts, out_dir / "data_issue.csv")

    # 6. Campaign ROI & Evaluation Metrics
    print("\n[Step 6/6] Computing Campaign Performance & ROI...")
    issue_entities = {i.entity_id for i in detected_issues}
    reconciler = FinancialReconciler(reporting_currency=config.reporting_currency)
    camp_perf = reconciler.calculate_campaign_performance(
        campaigns=dataset.campaigns,
        cost_records=dataset.cost_records,
        attribution_results=attr_exec.attribution_results,
        detected_issue_entities=issue_entities,
    )
    camp_perf_dicts = [c.to_dict() for c in camp_perf]
    write_table_csv(camp_perf_dicts, out_dir / "campaign_performance.csv")

    # Overall evaluation metrics comparing against ground truth
    pipeline_metrics = compute_pipeline_metrics(
        detected_issues=detected_issues,
        ground_truth=ground_truth,
        campaign_performances=camp_perf,
        orders=dataset.orders,
        attribution_results=attr_exec.attribution_results,
        reconciliation_passed=recon_all_pass,
    )

    metrics_file = out_dir / "evaluation_metrics.json"
    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump(pipeline_metrics.to_dict(), f, indent=2)

    recon_file = out_dir / "reconciliation_report.json"
    with open(recon_file, "w", encoding="utf-8") as f:
        json.dump(recon_summaries, f, indent=2)

    # Export seed.sql
    from src.attribution.export.sql_export import export_dataset_to_sql_seed
    from src.attribution.export.checksums import compute_file_sha256, generate_checksums_file
    print("\nExporting SQL seed statements to seed.sql...")
    export_dataset_to_sql_seed(
        dataset=dataset,
        output_path=out_dir / "seed.sql",
        extra_tables={
            "attribution_result": attr_exec.attribution_results,
            "attribution_touchpoint": attr_exec.attribution_touchpoints,
            "data_issue": detected_issue_dicts,
        },
    )

    # Generate checksums file
    generate_checksums_file(out_dir)

    # Compute checksum map for manifest
    checksum_map = {}
    for f in sorted(out_dir.glob("*.csv")):
        checksum_map[f.name] = compute_file_sha256(f)

    # Export manifest.json
    manifest = {
        "run_id": run_id,
        "generator_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seed": config.seed,
        "dataset_scale": config.dataset_scale,
        "config_hash": config.get_config_hash(),
        "reporting_currency": config.reporting_currency,
        "conversion_window_days": config.conversion_window_days,
        "validation_status": val_report.overall_status,
        "reconciliation_status": "PASS" if recon_all_pass else "FAIL",
        "row_counts": {
            **dataset.get_row_counts(),
            "attribution_result": len(attr_exec.attribution_results),
            "attribution_touchpoint": len(attr_exec.attribution_touchpoints),
            "data_issue": len(detected_issues),
        },
        "checksums": checksum_map,
    }
    manifest_file = out_dir / "manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)

    # Print Executive Summary Table
    exc = pipeline_metrics.exception_metrics
    print("\n================================================================================")
    print("PIPELINE EXECUTION SUMMARY")
    print("================================================================================")
    print(f"Exception Detection Precision : {exc.precision * 100:.2f}%")
    print(f"Exception Detection Recall    : {exc.recall * 100:.2f}%")
    print(f"Exception Detection F1 Score  : {exc.f1_score * 100:.2f}%")
    print(f"Attribution Coverage Rate     : {pipeline_metrics.attribution_coverage_rate * 100:.2f}%")
    print(f"ROI Availability Rate         : {pipeline_metrics.roi_availability_rate * 100:.2f}%")
    print(f"Reconciliation Pass Rate      : {pipeline_metrics.reconciliation_pass_rate * 100:.2f}%")
    print("--------------------------------------------------------------------------------")
    print("Top Campaigns by Linear Attributed ROI:")
    sorted_cmps = sorted(
        [c for c in camp_perf if c.linear_roi is not None],
        key=lambda x: x.linear_roi or -999,
        reverse=True,
    )[:5]
    print(f"{'Campaign ID':<16} {'Spend (INR)':>12} {'Linear Rev':>14} {'Linear ROI':>12}")
    for c in sorted_cmps:
        print(f"{c.campaign_id:<16} {c.actual_cost:>12,.2f} {c.linear_revenue:>14,.2f} {c.linear_roi:>11.2f}%")
    print("================================================================================")
    print(f"Pipeline outputs exported to {out_dir.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

