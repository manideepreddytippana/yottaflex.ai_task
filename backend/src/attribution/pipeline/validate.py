"""Automated validation engine enforcing structural, temporal, and financial invariants."""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal
import json
from pathlib import Path
from typing import Any

from src.attribution.ids import (
    is_valid_audience_id,
    is_valid_campaign_id,
    is_valid_channel_id,
    is_valid_contact_id,
    is_valid_cost_id,
    is_valid_creative_id,
    is_valid_lead_id,
    is_valid_opportunity_id,
    is_valid_order_id,
    is_valid_session_id,
    is_valid_touchpoint_id,
)


@dataclass
class ValidationCheckResult:
    check_name: str
    entity_name: str
    records_checked: int
    failure_count: int
    status: str  # PASS, FAIL, WARNING
    details: dict[str, Any]


@dataclass
class ValidationReport:
    overall_status: str
    total_checks: int
    passed_checks: int
    failed_checks: int
    executed_at: str
    findings: list[ValidationCheckResult]

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_status": self.overall_status,
            "total_checks": self.total_checks,
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
            "executed_at": self.executed_at,
            "findings": [asdict(f) for f in self.findings],
        }


def read_csv_table(data_dir: Path, filename: str) -> list[dict[str, str]]:
    p = data_dir / filename
    if not p.is_file():
        return []
    with open(p, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class DataValidator:
    """Validator implementing Section 13 rules against CSV data directory or dictionary tables."""

    def __init__(self, data_dir: Path | str) -> None:
        self.data_dir = Path(data_dir)
        self.findings: list[ValidationCheckResult] = []
        self._load_tables()

    def _load_tables(self) -> None:
        self.channels = read_csv_table(self.data_dir, "channel.csv")
        self.creatives = read_csv_table(self.data_dir, "creative.csv")
        self.audiences = read_csv_table(self.data_dir, "audience.csv")
        self.campaigns = read_csv_table(self.data_dir, "campaign.csv")
        self.campaign_creatives = read_csv_table(self.data_dir, "campaign_creative.csv")
        self.campaign_audiences = read_csv_table(self.data_dir, "campaign_audience.csv")
        self.contacts = read_csv_table(self.data_dir, "contact.csv")
        self.touchpoints = read_csv_table(self.data_dir, "touchpoint.csv")
        self.web_sessions = read_csv_table(self.data_dir, "web_session.csv")
        self.leads = read_csv_table(self.data_dir, "lead.csv")
        self.opportunities = read_csv_table(self.data_dir, "opportunity.csv")
        self.opportunity_events = read_csv_table(self.data_dir, "opportunity_event.csv")
        self.orders = read_csv_table(self.data_dir, "order.csv")
        self.order_events = read_csv_table(self.data_dir, "order_event.csv")
        self.cost_records = read_csv_table(self.data_dir, "cost_record.csv")

    def _add_check(
        self,
        name: str,
        entity: str,
        checked: int,
        failures: list[Any],
        status_on_failure: str = "FAIL",
    ) -> None:
        status = "PASS" if not failures else status_on_failure
        self.findings.append(
            ValidationCheckResult(
                check_name=name,
                entity_name=entity,
                records_checked=checked,
                failure_count=len(failures),
                status=status,
                details={"failures_sample": failures[:10] if failures else []},
            )
        )

    # 1. Structural Checks
    def validate_primary_keys(self) -> None:
        tables = [
            ("channel", self.channels, "channel_id"),
            ("creative", self.creatives, "creative_id"),
            ("audience", self.audiences, "audience_id"),
            ("campaign", self.campaigns, "campaign_id"),
            ("contact", self.contacts, "contact_id"),
            ("touchpoint", self.touchpoints, "touchpoint_id"),
            ("web_session", self.web_sessions, "session_id"),
            ("lead", self.leads, "lead_id"),
            ("opportunity", self.opportunities, "opportunity_id"),
            ("order", self.orders, "order_id"),
            ("cost_record", self.cost_records, "cost_record_id"),
        ]
        for tbl_name, rows, pk_field in tables:
            seen = set()
            duplicates = []
            for r in rows:
                val = r.get(pk_field)
                if not val or val in seen:
                    duplicates.append(val)
                seen.add(val)
            self._add_check(f"pk_uniqueness_{tbl_name}", tbl_name, len(rows), duplicates)

    def validate_id_formats(self) -> None:
        id_rules = [
            ("campaign", self.campaigns, "campaign_id", is_valid_campaign_id),
            ("contact", self.contacts, "contact_id", is_valid_contact_id),
            ("touchpoint", self.touchpoints, "touchpoint_id", is_valid_touchpoint_id),
            ("web_session", self.web_sessions, "session_id", is_valid_session_id),
            ("lead", self.leads, "lead_id", is_valid_lead_id),
            ("opportunity", self.opportunities, "opportunity_id", is_valid_opportunity_id),
            ("order", self.orders, "order_id", is_valid_order_id),
            ("cost_record", self.cost_records, "cost_record_id", is_valid_cost_id),
            ("channel", self.channels, "channel_id", is_valid_channel_id),
            ("creative", self.creatives, "creative_id", is_valid_creative_id),
            ("audience", self.audiences, "audience_id", is_valid_audience_id),
        ]
        for tbl, rows, col, validator in id_rules:
            invalid = [r[col] for r in rows if not validator(r.get(col, ""))]
            self._add_check(f"id_format_{tbl}", tbl, len(rows), invalid)

    def validate_foreign_keys(self) -> None:
        channels_set = {r["channel_id"] for r in self.channels}
        campaigns_set = {r["campaign_id"] for r in self.campaigns}
        contacts_set = {r["contact_id"] for r in self.contacts}
        sessions_set = {r["session_id"] for r in self.web_sessions}
        leads_set = {r["lead_id"] for r in self.leads}
        opps_set = {r["opportunity_id"] for r in self.opportunities}

        # campaign -> channel
        fk_fails = [c["campaign_id"] for c in self.campaigns if c["channel_id"] not in channels_set]
        self._add_check("fk_campaign_channel", "campaign", len(self.campaigns), fk_fails)

        # touchpoint -> contact / campaign / channel
        tp_fails = [
            t["touchpoint_id"]
            for t in self.touchpoints
            if (t.get("contact_id") and t["contact_id"] not in contacts_set)
            or (t.get("campaign_id") and t["campaign_id"] not in campaigns_set)
            or (t["channel_id"] not in channels_set)
        ]
        self._add_check("fk_touchpoint_parents", "touchpoint", len(self.touchpoints), tp_fails)

        # session -> contact / campaign
        sess_fails = [
            s["session_id"]
            for s in self.web_sessions
            if (s.get("contact_id") and s["contact_id"] not in contacts_set)
            or (s.get("campaign_id") and s["campaign_id"] not in campaigns_set)
        ]
        self._add_check("fk_session_parents", "web_session", len(self.web_sessions), sess_fails)

        # lead -> contact / session
        lead_fails = [
            l["lead_id"]
            for l in self.leads
            if l["contact_id"] not in contacts_set
            or (l.get("session_id") and l["session_id"] not in sessions_set)
        ]
        self._add_check("fk_lead_parents", "lead", len(self.leads), lead_fails)

        # opportunity -> lead
        opp_fails = [o["opportunity_id"] for o in self.opportunities if o["lead_id"] not in leads_set]
        self._add_check("fk_opportunity_lead", "opportunity", len(self.opportunities), opp_fails)

        # order -> opportunity / contact
        ord_fails = [
            o["order_id"]
            for o in self.orders
            if (o.get("opportunity_id") and o["opportunity_id"] not in opps_set)
            or o["contact_id"] not in contacts_set
        ]
        self._add_check("fk_order_parents", "order", len(self.orders), ord_fails)

        # cost_record -> campaign
        cost_fails = [c["cost_record_id"] for c in self.cost_records if c["campaign_id"] not in campaigns_set]
        self._add_check("fk_cost_campaign", "cost_record", len(self.cost_records), cost_fails)

    # 2. Temporal Checks
    def validate_temporal_sequences(self) -> None:
        # Campaign start_at <= end_at
        cmp_fails = [
            c["campaign_id"]
            for c in self.campaigns
            if datetime.fromisoformat(c["start_at"]) > datetime.fromisoformat(c["end_at"])
        ]
        self._add_check("temporal_campaign_dates", "campaign", len(self.campaigns), cmp_fails)

        # WebSession ended_at >= started_at
        sess_fails = [
            s["session_id"]
            for s in self.web_sessions
            if s.get("ended_at")
            and datetime.fromisoformat(s["ended_at"]) < datetime.fromisoformat(s["started_at"])
        ]
        self._add_check("temporal_session_dates", "web_session", len(self.web_sessions), sess_fails)

        # Lead qualification_at >= created_at
        lead_fails = [
            l["lead_id"]
            for l in self.leads
            if l.get("qualification_at")
            and datetime.fromisoformat(l["qualification_at"]) < datetime.fromisoformat(l["created_at"])
        ]
        self._add_check("temporal_lead_dates", "lead", len(self.leads), lead_fails)

        # Opportunity closed_at >= created_at
        opp_fails = [
            o["opportunity_id"]
            for o in self.opportunities
            if o.get("closed_at")
            and datetime.fromisoformat(o["closed_at"]) < datetime.fromisoformat(o["created_at"])
        ]
        self._add_check("temporal_opportunity_closed", "opportunity", len(self.opportunities), opp_fails)

        # Lead vs Opportunity
        leads_map = {l["lead_id"]: datetime.fromisoformat(l["created_at"]) for l in self.leads}
        opp_lead_fails = [
            o["opportunity_id"]
            for o in self.opportunities
            if o["lead_id"] in leads_map
            and datetime.fromisoformat(o["created_at"]) < leads_map[o["lead_id"]]
        ]
        self._add_check("temporal_opp_after_lead", "opportunity", len(self.opportunities), opp_lead_fails)

    # 3. Financial Checks
    def validate_financial_invariants(self) -> None:
        # Non-negative amounts
        cmp_neg = [c["campaign_id"] for c in self.campaigns if Decimal(c["budget_amount"]) < 0]
        self._add_check("financial_campaign_budget_positive", "campaign", len(self.campaigns), cmp_neg)

        opp_neg = [o["opportunity_id"] for o in self.opportunities if Decimal(o["expected_value"]) < 0]
        self._add_check("financial_opp_value_positive", "opportunity", len(self.opportunities), opp_neg)

        cost_neg = [c["cost_record_id"] for c in self.cost_records if Decimal(c["amount"]) < 0]
        self._add_check("financial_cost_positive", "cost_record", len(self.cost_records), cost_neg)

        # Order net_revenue = gross - refund and refund <= gross
        ord_fails = []
        for o in self.orders:
            gross = Decimal(o["gross_amount"])
            refund = Decimal(o["refund_amount"])
            net = Decimal(o["net_revenue"])
            if refund < 0 or refund > gross or net != (gross - refund):
                ord_fails.append(o["order_id"])
        self._add_check("financial_order_net_revenue", "order", len(self.orders), ord_fails)

    # 4. Lifecycle & Event Consistency
    def validate_lifecycle_consistency(self) -> None:
        # Opportunity latest event matches current status
        opp_events_by_id: dict[str, list[dict[str, str]]] = {}
        for ev in self.opportunity_events:
            opp_events_by_id.setdefault(ev["opportunity_id"], []).append(ev)

        mismatches = []
        for opp in self.opportunities:
            evs = opp_events_by_id.get(opp["opportunity_id"], [])
            if evs:
                latest = max(evs, key=lambda e: datetime.fromisoformat(e["occurred_at"]))
                if latest.get("new_status") and latest["new_status"] != opp["status"]:
                    mismatches.append(opp["opportunity_id"])
        self._add_check("lifecycle_opp_event_consistency", "opportunity", len(self.opportunities), mismatches)

    def execute_all(self) -> ValidationReport:
        self.findings.clear()
        self.validate_primary_keys()
        self.validate_id_formats()
        self.validate_foreign_keys()
        self.validate_temporal_sequences()
        self.validate_financial_invariants()
        self.validate_lifecycle_consistency()

        failed = sum(1 for f in self.findings if f.status == "FAIL")
        passed = sum(1 for f in self.findings if f.status == "PASS")
        overall = "PASS" if failed == 0 else "FAIL"

        return ValidationReport(
            overall_status=overall,
            total_checks=len(self.findings),
            passed_checks=passed,
            failed_checks=failed,
            executed_at=datetime.now().isoformat(),
            findings=self.findings,
        )

