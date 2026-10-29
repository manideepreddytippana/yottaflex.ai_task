"""JSON export utilities for exporting entities in structured JSON format."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.attribution.generator.orchestrator import GeneratedDataset


def export_dataset_to_json(
    dataset: GeneratedDataset,
    output_dir: Path | str,
    extra_tables: dict[str, list[dict[str, Any]]] | None = None,
) -> dict[str, Path]:
    """Export each table to an individual JSON file with sorted keys."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    file_mapping: dict[str, list[dict[str, Any]]] = {
        "channel.json": dataset.channels,
        "creative.json": dataset.creatives,
        "audience.json": dataset.audiences,
        "campaign.json": dataset.campaigns,
        "campaign_creative.json": dataset.campaign_creatives,
        "campaign_audience.json": dataset.campaign_audiences,
        "contact.json": dataset.contacts,
        "touchpoint.json": dataset.touchpoints,
        "web_session.json": dataset.web_sessions,
        "lead.json": dataset.leads,
        "opportunity.json": dataset.opportunities,
        "opportunity_event.json": dataset.opportunity_events,
        "order.json": dataset.orders,
        "order_event.json": dataset.order_events,
        "cost_record.json": dataset.cost_records,
    }

    if extra_tables:
        for tbl_name, tbl_rows in extra_tables.items():
            file_mapping[f"{tbl_name}.json"] = tbl_rows

    result_paths = {}
    for filename, table_data in file_mapping.items():
        file_path = out / filename
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(table_data, f, indent=2, sort_keys=True)
        result_paths[filename] = file_path

    return result_paths

