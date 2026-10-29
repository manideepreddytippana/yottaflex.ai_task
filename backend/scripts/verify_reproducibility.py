"""Reproducibility verification script: Executes two independent runs with identical seed/config and validates bit-for-bit parity."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.attribution.config import load_config
from src.attribution.export.checksums import compute_file_sha256, generate_checksums_file
from src.attribution.export.csv_export import export_dataset_to_csv, write_table_csv
from src.attribution.generator.anomalies import export_ground_truth, inject_anomalies_and_build_ground_truth
from src.attribution.generator.orchestrator import generate_dataset
from src.attribution.ids import DeterministicIDGenerator
from src.attribution.pipeline.attribution import AttributionEngine


def run_pipeline_for_reproducibility(config_path: str, output_dir: Path) -> dict[str, Any]:
    """Execute clean pipeline run producing normalized artifacts."""
    output_dir.mkdir(parents=True, exist_ok=True)
    config = load_config(config_path)

    id_gen = DeterministicIDGenerator(year=2026)
    dataset = generate_dataset(config)
    dataset, ground_truth = inject_anomalies_and_build_ground_truth(dataset, id_gen, config)

    # Export entities
    export_dataset_to_csv(dataset, output_dir)
    export_ground_truth(ground_truth, output_dir / "ground_truth.csv")

    # Attribution results
    run_id = f"RUN-{config.seed}-{config.dataset_scale}"
    engine = AttributionEngine(lookback_window_days=config.conversion_window_days, run_id=run_id)
    attr_exec = engine.compute_attribution(dataset.orders, dataset.touchpoints)
    write_table_csv(attr_exec.attribution_results, output_dir / "attribution_result.csv")
    write_table_csv(attr_exec.attribution_touchpoints, output_dir / "attribution_touchpoint.csv")

    generate_checksums_file(output_dir)

    checksums = {}
    for f in sorted(output_dir.glob("*.csv")):
        checksums[f.name] = compute_file_sha256(f)

    return {
        "row_counts": dataset.get_row_counts(),
        "checksums": checksums,
        "ground_truth_count": len(ground_truth),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify pipeline reproducibility across two identical runs")
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default="config/starter.yaml",
        help="Path to YAML configuration file",
    )
    parser.add_argument(
        "--dir-a",
        type=str,
        default="data/generated/run_A",
        help="Destination directory for Run A",
    )
    parser.add_argument(
        "--dir-b",
        type=str,
        default="data/generated/run_B",
        help="Destination directory for Run B",
    )
    parser.add_argument(
        "--keep-dirs",
        action="store_true",
        default=False,
        help="Keep temporary run directories after check",
    )
    args = parser.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.is_file():
        cfg_path = PROJECT_ROOT / args.config

    dir_a = Path(args.dir_a)
    if not dir_a.is_absolute() and not dir_a.is_dir():
        dir_a = PROJECT_ROOT / args.dir_a

    dir_b = Path(args.dir_b)
    if not dir_b.is_absolute() and not dir_b.is_dir():
        dir_b = PROJECT_ROOT / args.dir_b

    print("================================================================================")
    print("REPRODUCIBILITY VERIFICATION SUITE")
    print(f"Config: {cfg_path}")
    print("================================================================================")

    print("\nExecuting Run A...")
    res_a = run_pipeline_for_reproducibility(str(cfg_path), dir_a)
    print(f"  -> Run A completed with {len(res_a['checksums'])} files hashed")

    print("\nExecuting Run B (same seed, fresh memory state)...")
    res_b = run_pipeline_for_reproducibility(str(cfg_path), dir_b)
    print(f"  -> Run B completed with {len(res_b['checksums'])} files hashed")

    print("\nComparing Run A vs Run B:")
    print("--------------------------------------------------------------------------------")
    print(f"{'Entity File':<32} {'Run A SHA-256':<20} {'Run B SHA-256':<20} {'Match':>6}")
    print("--------------------------------------------------------------------------------")

    all_matched = True
    mismatches: list[str] = []

    files_a = set(res_a["checksums"].keys())
    files_b = set(res_b["checksums"].keys())

    if files_a != files_b:
        print(f"Error: Generated file list differs: {files_a.symmetric_difference(files_b)}")
        all_matched = False

    for fname in sorted(files_a.intersection(files_b)):
        hash_a = res_a["checksums"][fname]
        hash_b = res_b["checksums"][fname]
        is_match = hash_a == hash_b
        if not is_match:
            all_matched = False
            mismatches.append(fname)
        status_str = "PASS" if is_match else "FAIL"
        print(f"{fname:<32} {hash_a[:16]}...   {hash_b[:16]}...   {status_str:>6}")

    print("--------------------------------------------------------------------------------")
    print(f"Ground Truth Count Match : {res_a['ground_truth_count']} == {res_b['ground_truth_count']} ({'PASS' if res_a['ground_truth_count'] == res_b['ground_truth_count'] else 'FAIL'})")
    print(f"Entity Row Counts Match  : {'PASS' if res_a['row_counts'] == res_b['row_counts'] else 'FAIL'}")
    print(f"Overall Reproducibility  : {'BIT-FOR-BIT IDENTICAL (PASS)' if all_matched else 'FAILED'}")
    print("================================================================================")

    if not args.keep_dirs:
        shutil.rmtree(dir_a, ignore_errors=True)
        shutil.rmtree(dir_b, ignore_errors=True)

    return 0 if all_matched else 1


if __name__ == "__main__":
    sys.exit(main())

