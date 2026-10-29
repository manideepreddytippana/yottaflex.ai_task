"""Command-line validation runner for generated datasets."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.attribution.pipeline.validate import DataValidator


def main() -> int:
    parser = argparse.ArgumentParser(description="Run validation checks on generated dataset")
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default="data/generated/starter",
        help="Input directory containing entity CSV files",
    )
    parser.add_argument(
        "--output-report",
        "-o",
        type=str,
        default=None,
        help="Optional destination path for validation_summary.json (defaults to input dir)",
    )
    args = parser.parse_args()

    input_dir = Path(args.input)
    if not input_dir.is_dir() and not input_dir.is_absolute():
        input_dir = PROJECT_ROOT / args.input
    if not input_dir.is_dir():
        print(f"Error: Directory not found: {input_dir}", file=sys.stderr)
        return 1

    print(f"Running validation checks on {input_dir}...")
    validator = DataValidator(input_dir)
    report = validator.execute_all()

    # Print summary table
    print("\n--------------------------------------------------------------------------------------")
    print(f"{'Check Name':<38} {'Entity':<18} {'Checked':>10} {'Failures':>10} {'Status':>8}")
    print("--------------------------------------------------------------------------------------")
    for f in report.findings:
        print(f"{f.check_name:<38} {f.entity_name:<18} {f.records_checked:>10,} {f.failure_count:>10,} {f.status:>8}")
    print("--------------------------------------------------------------------------------------")
    print(f"Overall Status: {report.overall_status} ({report.passed_checks}/{report.total_checks} checks passed)")
    print("--------------------------------------------------------------------------------------")

    # Export validation_summary.json and validation_result.csv
    out_dir = Path(args.output_report) if args.output_report else input_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    summary_file = out_dir / "validation_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, indent=2)
    print(f"Validation summary written to: {summary_file}")

    csv_file = out_dir / "validation_result.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["check_name", "entity_name", "records_checked", "failure_count", "status", "details"],
        )
        writer.writeheader()
        for finding in report.findings:
            writer.writerow({
                "check_name": finding.check_name,
                "entity_name": finding.entity_name,
                "records_checked": finding.records_checked,
                "failure_count": finding.failure_count,
                "status": finding.status,
                "details": json.dumps(finding.details),
            })
    print(f"Validation findings written to: {csv_file}")

    return 0 if report.overall_status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

