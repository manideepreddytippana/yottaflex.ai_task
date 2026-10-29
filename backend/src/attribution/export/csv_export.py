    """CSV export utilities for serializing generated datasets."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from src.attribution.generator.orchestrator import GeneratedDataset


def write_table_csv(rows: list[dict[str, Any]], output_path: Path) -> None:
    """Write list of row dictionaries to CSV with consistent ordering."""
    if not rows:
        output_path.write_text("", encoding="utf-8")
        return

    # Extract fieldnames from first row
    fieldnames = list(rows[0].keys())

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            # Serialize JSON dictionaries to JSON string for CSV compatibility
            clean_row = {}
            for k, v in row.items():
                if isinstance(v, (dict, list)):
                    clean_row[k] = json.dumps(v, sort_keys=True)
                else:
                    clean_row[k] = v if v is not None else ""
            writer.writerow(clean_row)


def export_dataset_to_csv(dataset: GeneratedDataset, output_dir: Path | str) -> dict[str, Path]:
    """Export all tables in dataset to CSV files in target directory."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    file_mapping = {
        "channel.csv": dataset.channels,
        "creative.csv": dataset.creatives,
        "audience.csv": dataset.audiences,
        "campaign.csv": dataset.campaigns,
        "campaign_creative.csv": dataset.campaign_creatives,
        "campaign_audience.csv": dataset.campaign_audiences,
        "contact.csv": dataset.contacts,
        "touchpoint.csv": dataset.touchpoints,
        "web_session.csv": dataset.web_sessions,
        "lead.csv": dataset.leads,
        "opportunity.csv": dataset.opportunities,
        "opportunity_event.csv": dataset.opportunity_events,
        "order.csv": dataset.orders,
        "order_event.csv": dataset.order_events,
        "cost_record.csv": dataset.cost_records,
    }

    result_paths = {}
    for filename, table_data in file_mapping.items():
        file_path = out / filename
        write_table_csv(table_data, file_path)
        result_paths[filename] = file_path

    # Export row_counts.json
    row_counts_path = out / "row_counts.json"
    with open(row_counts_path, "w", encoding="utf-8") as f:
        json.dump(dataset.get_row_counts(), f, indent=2, sort_keys=True)
    result_paths["row_counts.json"] = row_counts_path

    return result_paths

