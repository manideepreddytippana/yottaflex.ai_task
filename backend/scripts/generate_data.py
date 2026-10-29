"""Command-line script for deterministic synthetic data generation."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.attribution.config import load_config
from src.attribution.export.checksums import generate_checksums_file
from src.attribution.export.csv_export import export_dataset_to_csv
from src.attribution.generator.orchestrator import generate_dataset



def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic Synthetic Data Generator")
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default="config/starter.yaml",
        help="Path to YAML configuration file (default: config/starter.yaml)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="data/generated/starter",
        help="Output directory path (default: data/generated/starter)",
    )
    args = parser.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.is_file():
        cfg_path = PROJECT_ROOT / args.config

    print(f"Loading configuration from {cfg_path}...")
    config = load_config(cfg_path)
    print(f"Seed: {config.seed} | Scale: {config.dataset_scale} | Reporting Currency: {config.reporting_currency}")

    start_time = datetime.now(timezone.utc)
    print("Generating synthetic entities...")
    dataset = generate_dataset(config)

    out_dir = Path(args.output)
    if not out_dir.is_dir() and not out_dir.is_absolute():
        out_dir = PROJECT_ROOT / args.output
    print(f"Exporting tables to CSV in {out_dir}...")
    export_dataset_to_csv(dataset, out_dir)

    print("Generating SHA-256 checksums...")
    generate_checksums_file(out_dir)

    # Generate manifest.json
    manifest = {
        "generator_version": "1.0.0",
        "generated_at": start_time.isoformat(),
        "seed": config.seed,
        "dataset_scale": config.dataset_scale,
        "config_hash": config.get_config_hash(),
        "reporting_currency": config.reporting_currency,
        "conversion_window_days": config.conversion_window_days,
        "row_counts": dataset.get_row_counts(),
    }
    manifest_path = out_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)

    print("\nGeneration completed successfully!")
    print("-----------------------------------------")
    print(f"{'Entity':<24} {'Count':>10}")
    print("-----------------------------------------")
    for entity, count in dataset.get_row_counts().items():
        print(f"{entity:<24} {count:>10,}")
    print("-----------------------------------------")
    print(f"Output Directory: {out_dir.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
