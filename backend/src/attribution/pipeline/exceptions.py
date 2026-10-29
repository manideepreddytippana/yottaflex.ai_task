"""Exception Detection Engine: Identifies data quality anomalies without ground-truth leakage."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from src.attribution.ids import DeterministicIDGenerator


@dataclass
class DetectedIssue:
    issue_id: str
    run_id: str
    entity_type: str
    entity_id: str
    issue_type: str
    severity: str  # INFO, LOW, MEDIUM, HIGH, CRITICAL
    detected_at: str
    decision: str
    resolution_status: str  # OPEN, ACKNOWLEDGED, RESOLVED, ACCEPTED
    details_json: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ExceptionDetector:
    """Scans raw datasets and identifies anomalies adhering to Section 7.5."""

    def __init__(self, run_id: str = "RUN-DEFAULT") -> None:
        self.run_id = run_id
        self.id_gen = DeterministicIDGenerator(year=2026)

    def detect_all(
        self,
        orders: list[dict[str, Any]],
        touchpoints: list[dict[str, Any]],
        cost_records: list[dict[str, Any]],
        campaigns: list[dict[str, Any]],
        web_sessions: list[dict[str, Any]],
        reporting_currency: str = "INR",
        detected_at: str = "2026-10-31T23:59:59+00:00",
    ) -> list[DetectedIssue]:
        """Execute full exception detection suite across entities."""
        issues: list[DetectedIssue] = []
        now_iso = detected_at

        # 1. Detect Duplicate Revenue
        issues.extend(self._detect_duplicate_revenue(orders, now_iso))

        # 2. Detect Post-Conversion Touchpoints
        issues.extend(self._detect_post_conversion_touches(orders, touchpoints, now_iso))

        # 3. Detect Currency Mismatches / Missing FX
        issues.extend(self._detect_currency_mismatches(cost_records, reporting_currency, now_iso))

        # 4. Detect Missing Campaign Costs
        issues.extend(self._detect_missing_costs(campaigns, cost_records, now_iso))

        # 5. Detect Unsupported Identity Links
        issues.extend(self._detect_unsupported_identity_links(web_sessions, now_iso))

        return issues

    def _detect_duplicate_revenue(self, orders: list[dict[str, Any]], now_iso: str) -> list[DetectedIssue]:
        issues: list[DetectedIssue] = []
        txn_map: dict[str, list[dict[str, Any]]] = {}
        for o in orders:
            key = o.get("economic_transaction_key")
            if key:
                txn_map.setdefault(key, []).append(o)

        for key, matching_orders in txn_map.items():
            if len(matching_orders) > 1:
                # First order by ordered_at is primary; subsequent orders are duplicates
                sorted_orders = sorted(matching_orders, key=lambda x: (x["ordered_at"], x["order_id"]))
                primary = sorted_orders[0]
                for dup in sorted_orders[1:]:
                    issues.append(
                        DetectedIssue(
                            issue_id=self.id_gen.issue_id(),
                            run_id=self.run_id,
                            entity_type="order",
                            entity_id=dup["order_id"],
                            issue_type="DUPLICATE_REVENUE",
                            severity="CRITICAL",
                            detected_at=now_iso,
                            decision="COUNT_ONCE_FLAG_DUPLICATE",
                            resolution_status="OPEN",
                            details_json={
                                "economic_transaction_key": key,
                                "primary_order_id": primary["order_id"],
                                "duplicate_net_revenue": dup["net_revenue"],
                            },
                        )
                    )
        return issues

    def _detect_post_conversion_touches(
        self,
        orders: list[dict[str, Any]],
        touchpoints: list[dict[str, Any]],
        now_iso: str,
    ) -> list[DetectedIssue]:
        issues: list[DetectedIssue] = []
        # Contact conversions
        contact_orders: dict[str, list[datetime]] = {}
        for o in orders:
            cid = o.get("contact_id")
            if cid and o.get("status") == "PAID":
                contact_orders.setdefault(cid, []).append(datetime.fromisoformat(o["ordered_at"]))

        for t in touchpoints:
            cid = t.get("contact_id")
            if not cid or cid not in contact_orders:
                continue

            t_dt = datetime.fromisoformat(t["occurred_at"])
            # If touchpoint occurred after any conversion for this contact
            for ord_dt in contact_orders[cid]:
                if t_dt > ord_dt:
                    issues.append(
                        DetectedIssue(
                            issue_id=self.id_gen.issue_id(),
                            run_id=self.run_id,
                            entity_type="touchpoint",
                            entity_id=t["touchpoint_id"],
                            issue_type="POST_CONVERSION_TOUCH",
                            severity="MEDIUM",
                            detected_at=now_iso,
                            decision="EXCLUDE_FROM_ATTRIBUTION",
                            resolution_status="OPEN",
                            details_json={
                                "contact_id": cid,
                                "touch_occurred_at": t["occurred_at"],
                                "conversion_ordered_at": ord_dt.isoformat(),
                            },
                        )
                    )
                    break
        return issues

    def _detect_currency_mismatches(
        self,
        cost_records: list[dict[str, Any]],
        reporting_currency: str,
        now_iso: str,
    ) -> list[DetectedIssue]:
        issues: list[DetectedIssue] = []
        for c in cost_records:
            curr = c.get("currency")
            fx_rate = c.get("exchange_rate_to_reporting")
            reporting_amt = c.get("reporting_amount")

            if curr != reporting_currency:
                if fx_rate is None or reporting_amt is None or float(fx_rate) <= 0:
                    issues.append(
                        DetectedIssue(
                            issue_id=self.id_gen.issue_id(),
                            run_id=self.run_id,
                            entity_type="cost_record",
                            entity_id=c["cost_record_id"],
                            issue_type="CURRENCY_MISMATCH",
                            severity="HIGH",
                            detected_at=now_iso,
                            decision="BLOCK_ROI_FLAG_UNRESOLVED_FX",
                            resolution_status="OPEN",
                            details_json={
                                "campaign_id": c.get("campaign_id"),
                                "cost_currency": curr,
                                "reporting_currency": reporting_currency,
                                "exchange_rate": fx_rate,
                            },
                        )
                    )
        return issues

    def _detect_missing_costs(
        self,
        campaigns: list[dict[str, Any]],
        cost_records: list[dict[str, Any]],
        now_iso: str,
    ) -> list[DetectedIssue]:
        issues: list[DetectedIssue] = []
        cmps_with_costs = {c["campaign_id"] for c in cost_records if float(c.get("amount", 0)) > 0}

        for cmp in campaigns:
            if cmp["status"] in ("ACTIVE", "COMPLETED"):
                cid = cmp["campaign_id"]
                if cid not in cmps_with_costs:
                    issues.append(
                        DetectedIssue(
                            issue_id=self.id_gen.issue_id(),
                            run_id=self.run_id,
                            entity_type="campaign",
                            entity_id=cid,
                            issue_type="MISSING_CAMPAIGN_COST",
                            severity="HIGH",
                            detected_at=now_iso,
                            decision="MARK_INCOMPLETE_COST_ROI_UNAVAILABLE",
                            resolution_status="OPEN",
                            details_json={
                                "campaign_status": cmp["status"],
                                "budget_amount": cmp["budget_amount"],
                            },
                        )
                    )
        return issues

    def _detect_unsupported_identity_links(
        self,
        web_sessions: list[dict[str, Any]],
        now_iso: str,
    ) -> list[DetectedIssue]:
        issues: list[DetectedIssue] = []
        for s in web_sessions:
            cid = s.get("contact_id")
            evidence = s.get("identity_evidence", "NONE")
            is_anon = s.get("is_anonymous", False)

            # Anomaly: Session links to a contact, but is flagged anonymous or lacks evidence
            if cid and (is_anon or evidence in ("NONE", "UNKNOWN")):
                issues.append(
                    DetectedIssue(
                        issue_id=self.id_gen.issue_id(),
                        run_id=self.run_id,
                        entity_type="web_session",
                        entity_id=s["session_id"],
                        issue_type="UNSUPPORTED_IDENTITY_LINK",
                        severity="MEDIUM",
                        detected_at=now_iso,
                        decision="QUARANTINE_IDENTITY_LINK",
                        resolution_status="OPEN",
                        details_json={
                            "contact_id": cid,
                            "identity_evidence": evidence,
                            "is_anonymous": is_anon,
                        },
                    )
                )
        return issues

