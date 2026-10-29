"""SQL seed export generator for PostgreSQL."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.attribution.generator.orchestrator import GeneratedDataset


def escape_sql_val(val: Any) -> str:
    """Escape values for PostgreSQL INSERT statements."""
    if val is None:
        return "NULL"
    if isinstance(val, bool):
        return "TRUE" if val else "FALSE"
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, (dict, list)):
        dumped = json.dumps(val).replace("'", "''")
        return f"'{dumped}'::jsonb"
    s = str(val).replace("'", "''")
    return f"'{s}'"


def generate_sql_insert_statements(table_name: str, rows: list[dict[str, Any]]) -> list[str]:
    """Generate SQL INSERT statements for a list of entity dictionaries."""
    if not rows:
        return []

    # Quote table name if it's order (PostgreSQL keyword)
    quoted_table = f'"{table_name}"' if table_name == "order" else table_name
    fieldnames = list(rows[0].keys())
    columns_str = ", ".join(f'"{f}"' if f == "order" else f for f in fieldnames)

    statements = []
    # Batch in groups of 100 for clean SQL seed files
    batch_size = 100
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        values_list = []
        for row in batch:
            row_vals = [escape_sql_val(row.get(f)) for f in fieldnames]
            values_list.append(f"    ({', '.join(row_vals)})")
        stmt = f"INSERT INTO {quoted_table} ({columns_str}) VALUES\n" + ",\n".join(values_list) + ";"
        statements.append(stmt)

    return statements


def export_dataset_to_sql_seed(
    dataset: GeneratedDataset,
    output_path: Path | str,
    extra_tables: dict[str, list[dict[str, Any]]] | None = None,
) -> Path:
    """Generate complete seed.sql script in strict foreign-key dependency order."""
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    ordered_tables: list[tuple[str, list[dict[str, Any]]]] = [
        ("channel", dataset.channels),
        ("creative", dataset.creatives),
        ("audience", dataset.audiences),
        ("campaign", dataset.campaigns),
        ("campaign_creative", dataset.campaign_creatives),
        ("campaign_audience", dataset.campaign_audiences),
        ("contact", dataset.contacts),
        ("touchpoint", dataset.touchpoints),
        ("web_session", dataset.web_sessions),
        ("lead", dataset.leads),
        ("opportunity", dataset.opportunities),
        ("opportunity_event", dataset.opportunity_events),
        ("order", dataset.orders),
        ("order_event", dataset.order_events),
        ("cost_record", dataset.cost_records),
    ]

    if extra_tables:
        for tbl_name, tbl_rows in extra_tables.items():
            ordered_tables.append((tbl_name, tbl_rows))

    sql_lines = [
        "-- ============================================================================",
        "-- Marketing Campaign Attribution & ROI Analysis System - Seed Data",
        "-- Generated automatically. Do not edit directly.",
        "-- ============================================================================",
        "BEGIN;",
        "",
    ]

    for tbl_name, rows in ordered_tables:
        if not rows:
            continue
        sql_lines.append(f"-- Table: {tbl_name} ({len(rows)} records)")
        stmts = generate_sql_insert_statements(tbl_name, rows)
        sql_lines.extend(stmts)
        sql_lines.append("")

    sql_lines.append("COMMIT;")
    sql_lines.append("")

    out_file.write_text("\n".join(sql_lines), encoding="utf-8")
    return out_file

