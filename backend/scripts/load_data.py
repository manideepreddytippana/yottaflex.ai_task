"""Database loader script to ingest generated CSV datasets into PostgreSQL or SQLite."""

from __future__ import annotations

import argparse
import csv
from datetime import date, datetime
from decimal import Decimal
import json
from pathlib import Path
import sys
from typing import Any, Callable

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy.orm import Session
from src.attribution.db.models import (
    Audience,
    AttributionResult,
    AttributionTouchpoint,
    Campaign,
    CampaignAudience,
    CampaignCreative,
    Channel,
    Contact,
    CostRecord,
    Creative,
    DataIssue,
    Lead,
    Opportunity,
    OpportunityEvent,
    Order,
    OrderEvent,
    PipelineRun,
    Touchpoint,
    ValidationResult,
    WebSession,
)
from src.attribution.db.session import create_db_engine, get_session_factory, init_db


def parse_iso_datetime(val: str | None) -> datetime | None:
    if not val:
        return None
    return datetime.fromisoformat(val)


def parse_iso_date(val: str | None) -> date | None:
    if not val:
        return None
    return date.fromisoformat(val)


def parse_decimal(val: str | None) -> Decimal | None:
    if val is None or val == "":
        return None
    return Decimal(str(val))


def parse_bool(val: str | None, default: bool = False) -> bool:
    if val is None or val == "":
        return default
    return str(val).lower() in ("true", "1", "yes")


def parse_json(val: str | None) -> dict[str, Any] | None:
    if not val:
        return None
    try:
        return json.loads(val)
    except Exception:
        return None


def add_in_batches(session: Session, items: list[Any], batch_size: int = 5000) -> None:
    """Flush objects in batches to optimize memory and PostgreSQL bulk inserts."""
    for i in range(0, len(items), batch_size):
        session.add_all(items[i : i + batch_size])
        session.flush()


def read_csv_rows(csv_path: Path) -> list[dict[str, str]]:
    if not csv_path.is_file():
        return []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def load_dataset(input_dir: Path | str, db_url: str | None = None, clean: bool = True) -> dict[str, int]:
    """Load CSV tables into the database in foreign-key dependency order."""
    data_dir = Path(input_dir)
    if not data_dir.is_dir() and not data_dir.is_absolute():
        data_dir = PROJECT_ROOT / input_dir
    engine = create_db_engine(db_url)
    if clean:
        from src.attribution.db.session import drop_db
        drop_db(engine)
    init_db(engine)

    session_factory = get_session_factory(engine)
    session: Session = session_factory()

    loaded_counts: dict[str, int] = {}

    try:
        # 1. Channels
        ch_rows = read_csv_rows(data_dir / "channel.csv")
        channels = [
            Channel(
                channel_id=r["channel_id"],
                name=r["name"],
                channel_type=r["channel_type"],
                is_active=parse_bool(r.get("is_active"), True),
                created_at=parse_iso_datetime(r["created_at"]),
            )
            for r in ch_rows
        ]
        session.add_all(channels)
        session.flush()
        loaded_counts["channel"] = len(channels)

        # 2. Creatives
        cr_rows = read_csv_rows(data_dir / "creative.csv")
        creatives = [
            Creative(
                creative_id=r["creative_id"],
                name=r["name"],
                format=r["format"],
                version=r["version"],
                active_from=parse_iso_datetime(r["active_from"]),
                active_to=parse_iso_datetime(r.get("active_to")),
                metadata_json=parse_json(r.get("metadata_json")),
            )
            for r in cr_rows
        ]
        session.add_all(creatives)
        session.flush()
        loaded_counts["creative"] = len(creatives)

        # 3. Audiences
        aud_rows = read_csv_rows(data_dir / "audience.csv")
        audiences = [
            Audience(
                audience_id=r["audience_id"],
                name=r["name"],
                segment_type=r["segment_type"],
                criteria_json=parse_json(r.get("criteria_json")),
                effective_from=parse_iso_datetime(r["effective_from"]),
                effective_to=parse_iso_datetime(r.get("effective_to")),
            )
            for r in aud_rows
        ]
        session.add_all(audiences)
        session.flush()
        loaded_counts["audience"] = len(audiences)

        # 4. Campaigns
        cmp_rows = read_csv_rows(data_dir / "campaign.csv")
        campaigns = [
            Campaign(
                campaign_id=r["campaign_id"],
                name=r["name"],
                channel_id=r["channel_id"],
                budget_amount=parse_decimal(r["budget_amount"]),
                currency=r["currency"],
                start_at=parse_iso_datetime(r["start_at"]),
                end_at=parse_iso_datetime(r["end_at"]),
                status=r["status"],
                objective=r.get("objective") or None,
                created_at=parse_iso_datetime(r["created_at"]),
            )
            for r in cmp_rows
        ]
        session.add_all(campaigns)
        session.flush()
        loaded_counts["campaign"] = len(campaigns)

        # 5. Bridges
        cc_rows = read_csv_rows(data_dir / "campaign_creative.csv")
        cc_bridges = [
            CampaignCreative(
                campaign_id=r["campaign_id"],
                creative_id=r["creative_id"],
                effective_from=parse_iso_datetime(r["effective_from"]),
                effective_to=parse_iso_datetime(r.get("effective_to")),
            )
            for r in cc_rows
        ]
        session.add_all(cc_bridges)

        ca_rows = read_csv_rows(data_dir / "campaign_audience.csv")
        ca_bridges = [
            CampaignAudience(
                campaign_id=r["campaign_id"],
                audience_id=r["audience_id"],
                effective_from=parse_iso_datetime(r["effective_from"]),
                effective_to=parse_iso_datetime(r.get("effective_to")),
            )
            for r in ca_rows
        ]
        session.add_all(ca_bridges)
        session.flush()
        loaded_counts["campaign_creative"] = len(cc_bridges)
        loaded_counts["campaign_audience"] = len(ca_bridges)

        # 6. Contacts
        con_rows = read_csv_rows(data_dir / "contact.csv")
        contacts = [
            Contact(
                contact_id=r["contact_id"],
                created_at=parse_iso_datetime(r["created_at"]),
                region=r.get("region") or None,
                customer_segment=r.get("customer_segment") or None,
                consent_status=r["consent_status"],
                is_synthetic=parse_bool(r.get("is_synthetic"), True),
                identity_status=r["identity_status"],
            )
            for r in con_rows
        ]
        add_in_batches(session, contacts, 5000)
        loaded_counts["contact"] = len(contacts)

        # 7. Touchpoints
        tp_rows = read_csv_rows(data_dir / "touchpoint.csv")
        touchpoints = [
            Touchpoint(
                touchpoint_id=r["touchpoint_id"],
                contact_id=r.get("contact_id") or None,
                campaign_id=r.get("campaign_id") or None,
                channel_id=r["channel_id"],
                creative_id=r.get("creative_id") or None,
                occurred_at=parse_iso_datetime(r["occurred_at"]),
                touch_type=r["touch_type"],
                touch_mode=r["touch_mode"],
                source_event_id=r.get("source_event_id") or None,
                identity_evidence=r["identity_evidence"],
                issue_type=r.get("issue_type") or None,
                is_synthetic=parse_bool(r.get("is_synthetic"), True),
            )
            for r in tp_rows
        ]
        add_in_batches(session, touchpoints, 5000)
        loaded_counts["touchpoint"] = len(touchpoints)

        # 8. Web Sessions
        ws_rows = read_csv_rows(data_dir / "web_session.csv")
        web_sessions = [
            WebSession(
                session_id=r["session_id"],
                contact_id=r.get("contact_id") or None,
                campaign_id=r.get("campaign_id") or None,
                started_at=parse_iso_datetime(r["started_at"]),
                ended_at=parse_iso_datetime(r.get("ended_at")),
                source_channel_id=r.get("source_channel_id") or None,
                landing_path=r.get("landing_path") or None,
                identity_evidence=r["identity_evidence"],
                is_anonymous=parse_bool(r.get("is_anonymous"), False),
                issue_type=r.get("issue_type") or None,
            )
            for r in ws_rows
        ]
        add_in_batches(session, web_sessions, 5000)
        loaded_counts["web_session"] = len(web_sessions)

        # 9. Leads
        ld_rows = read_csv_rows(data_dir / "lead.csv")
        leads = [
            Lead(
                lead_id=r["lead_id"],
                contact_id=r["contact_id"],
                session_id=r.get("session_id") or None,
                created_at=parse_iso_datetime(r["created_at"]),
                status=r["status"],
                source_type=r["source_type"],
                qualification_at=parse_iso_datetime(r.get("qualification_at")),
                issue_type=r.get("issue_type") or None,
            )
            for r in ld_rows
        ]
        add_in_batches(session, leads, 5000)
        loaded_counts["lead"] = len(leads)

        # 10. Opportunities
        opp_rows = read_csv_rows(data_dir / "opportunity.csv")
        opportunities = [
            Opportunity(
                opportunity_id=r["opportunity_id"],
                lead_id=r["lead_id"],
                created_at=parse_iso_datetime(r["created_at"]),
                expected_value=parse_decimal(r["expected_value"]),
                currency=r["currency"],
                status=r["status"],
                closed_at=parse_iso_datetime(r.get("closed_at")),
                actual_closed_value=parse_decimal(r.get("actual_closed_value")),
                issue_type=r.get("issue_type") or None,
            )
            for r in opp_rows
        ]
        add_in_batches(session, opportunities, 5000)
        loaded_counts["opportunity"] = len(opportunities)

        # 11. Opportunity Events
        oe_rows = read_csv_rows(data_dir / "opportunity_event.csv")
        opp_events = [
            OpportunityEvent(
                opportunity_event_id=r["opportunity_event_id"],
                opportunity_id=r["opportunity_id"],
                event_type=r["event_type"],
                old_status=r.get("old_status") or None,
                new_status=r.get("new_status") or None,
                occurred_at=parse_iso_datetime(r["occurred_at"]),
                event_payload=parse_json(r.get("event_payload")),
                run_id=r.get("run_id") or None,
            )
            for r in oe_rows
        ]
        add_in_batches(session, opp_events, 5000)
        loaded_counts["opportunity_event"] = len(opp_events)

        # 12. Orders
        ord_rows = read_csv_rows(data_dir / "order.csv")
        orders = [
            Order(
                order_id=r["order_id"],
                opportunity_id=r.get("opportunity_id") or None,
                contact_id=r["contact_id"],
                ordered_at=parse_iso_datetime(r["ordered_at"]),
                status=r["status"],
                gross_amount=parse_decimal(r["gross_amount"]),
                refund_amount=parse_decimal(r["refund_amount"]),
                net_revenue=parse_decimal(r["net_revenue"]),
                currency=r["currency"],
                economic_transaction_key=r["economic_transaction_key"],
                issue_type=r.get("issue_type") or None,
            )
            for r in ord_rows
        ]
        add_in_batches(session, orders, 5000)
        loaded_counts["order"] = len(orders)

        # 13. Order Events
        orde_rows = read_csv_rows(data_dir / "order_event.csv")
        order_events = [
            OrderEvent(
                order_event_id=r["order_event_id"],
                order_id=r["order_id"],
                event_type=r["event_type"],
                old_status=r.get("old_status") or None,
                new_status=r.get("new_status") or None,
                occurred_at=parse_iso_datetime(r["occurred_at"]),
                event_payload=parse_json(r.get("event_payload")),
                run_id=r.get("run_id") or None,
            )
            for r in orde_rows
        ]
        add_in_batches(session, order_events, 5000)
        loaded_counts["order_event"] = len(order_events)

        # 14. Cost Records
        cost_rows = read_csv_rows(data_dir / "cost_record.csv")
        cost_records = [
            CostRecord(
                cost_record_id=r["cost_record_id"],
                campaign_id=r["campaign_id"],
                incurred_at=parse_iso_datetime(r["incurred_at"]),
                cost_type=r["cost_type"],
                amount=parse_decimal(r["amount"]),
                currency=r["currency"],
                exchange_rate_to_reporting=parse_decimal(r.get("exchange_rate_to_reporting")),
                reporting_amount=parse_decimal(r.get("reporting_amount")),
                rate_date=parse_iso_date(r.get("rate_date")),
                source_reference=r.get("source_reference") or None,
                issue_type=r.get("issue_type") or None,
            )
            for r in cost_rows
        ]
        add_in_batches(session, cost_records, 5000)
        loaded_counts["cost_record"] = len(cost_records)

        # 15. Pipeline Run (from manifest.json if present)
        manifest_path = data_dir / "manifest.json"
        if manifest_path.is_file():
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)
            run_id = manifest_data.get("run_id", "RUN-UNKNOWN")
            p_run = PipelineRun(
                run_id=run_id,
                started_at=parse_iso_datetime(manifest_data.get("generated_at")) or datetime.now(),
                completed_at=parse_iso_datetime(manifest_data.get("generated_at")),
                seed=int(manifest_data.get("seed", 20261022)),
                generator_version=str(manifest_data.get("generator_version", "1.0.0")),
                config_hash=str(manifest_data.get("config_hash", "")),
                dataset_scale=str(manifest_data.get("dataset_scale", "starter")),
                status=str(manifest_data.get("validation_status", "PASS")),
                row_counts_json=manifest_data.get("row_counts"),
                checksums_json=manifest_data.get("checksums"),
            )
            session.merge(p_run)
            session.flush()
            loaded_counts["pipeline_run"] = 1

        # 16. Attribution Results
        attr_rows = read_csv_rows(data_dir / "attribution_result.csv")
        if attr_rows:
            attribution_results = [
                AttributionResult(
                    attribution_result_id=r["attribution_result_id"],
                    order_id=r["order_id"],
                    campaign_id=r.get("campaign_id") or None,
                    model_name=r["model_name"],
                    model_version=r.get("model_version", "1.0.0"),
                    credit_share=parse_decimal(r["credit_share"]),
                    attributed_revenue=parse_decimal(r["attributed_revenue"]),
                    calculated_at=parse_iso_datetime(r["calculated_at"]),
                    decision_reason=r.get("decision_reason") or None,
                    run_id=r.get("run_id", "RUN-UNKNOWN"),
                    issue_type=r.get("issue_type") or None,
                )
                for r in attr_rows
            ]
            add_in_batches(session, attribution_results, 5000)
            loaded_counts["attribution_result"] = len(attribution_results)

        # 17. Attribution Touchpoints
        atrp_rows = read_csv_rows(data_dir / "attribution_touchpoint.csv")
        if atrp_rows:
            attribution_touchpoints = [
                AttributionTouchpoint(
                    attribution_result_id=r["attribution_result_id"],
                    touchpoint_id=r["touchpoint_id"],
                    contribution_weight=parse_decimal(r["contribution_weight"]),
                )
                for r in atrp_rows
            ]
            add_in_batches(session, attribution_touchpoints, 5000)
            loaded_counts["attribution_touchpoint"] = len(attribution_touchpoints)

        # 18. Data Issues
        issue_rows = read_csv_rows(data_dir / "data_issue.csv")
        if issue_rows:
            data_issues = [
                DataIssue(
                    issue_id=r["issue_id"],
                    run_id=r.get("run_id") or None,
                    entity_type=r["entity_type"],
                    entity_id=r["entity_id"],
                    issue_type=r["issue_type"],
                    severity=r.get("severity", "MEDIUM"),
                    detected_at=parse_iso_datetime(r["detected_at"]),
                    decision=r.get("decision") or None,
                    resolution_status=r.get("resolution_status", "OPEN"),
                    details_json=parse_json(r.get("details_json")),
                )
                for r in issue_rows
            ]
            add_in_batches(session, data_issues, 5000)
            loaded_counts["data_issue"] = len(data_issues)

        # 19. Validation Results
        val_rows = read_csv_rows(data_dir / "validation_result.csv")
        if val_rows:
            val_results = [
                ValidationResult(
                    validation_result_id=r.get("validation_result_id") or f"VAL-{idx+1:05d}",
                    run_id=r.get("run_id") or None,
                    check_name=r["check_name"],
                    entity_name=r["entity_name"],
                    records_checked=int(r["records_checked"]),
                    failure_count=int(r["failure_count"]),
                    status=r["status"],
                    details_json=parse_json(r.get("details")) or parse_json(r.get("details_json")),
                    executed_at=parse_iso_datetime(r.get("executed_at")) or datetime.now(),
                )
                for idx, r in enumerate(val_rows)
            ]
            session.add_all(val_results)
            session.flush()
            loaded_counts["validation_result"] = len(val_results)

        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    return loaded_counts


def main() -> int:
    parser = argparse.ArgumentParser(description="Load generated CSV dataset into database")
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default="data/generated/starter",
        help="Input directory containing entity CSV files",
    )
    parser.add_argument(
        "--db-url",
        type=str,
        default=None,
        help="Database URL (default: from env or local SQLite)",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        default=True,
        help="Clean and re-create database schema before loading (default: True)",
    )
    args = parser.parse_args()

    print(f"Loading data from {args.input}...")
    counts = load_dataset(args.input, args.db_url, clean=args.clean)
    print("\nDatabase load completed successfully!")
    print("-----------------------------------------")
    print(f"{'Table':<24} {'Loaded':>10}")
    print("-----------------------------------------")
    for tbl, count in counts.items():
        print(f"{tbl:<24} {count:>10,}")
    print("-----------------------------------------")
    return 0


if __name__ == "__main__":
    sys.exit(main())
