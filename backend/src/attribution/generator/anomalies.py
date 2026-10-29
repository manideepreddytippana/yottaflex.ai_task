"""Controlled anomaly injection engine and ground-truth dataset generator.

Implements the 5 required anomaly scenarios:
1. DUPLICATE_REVENUE: Two orders sharing the same economic_transaction_key.
2. POST_CONVERSION_TOUCH: Touchpoint timestamp > order conversion timestamp.
3. CURRENCY_MISMATCH: Cost record in foreign currency without valid FX rate.
4. MISSING_CAMPAIGN_COST: Active campaign with incomplete or missing cost coverage.
5. UNSUPPORTED_IDENTITY_LINK: Web session with unsupported/missing identity evidence linked to contact.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from src.attribution.config import SystemConfig
from src.attribution.generator.orchestrator import GeneratedDataset
from src.attribution.ids import DeterministicIDGenerator


@dataclass
class GroundTruthRecord:
    ground_truth_id: str
    entity_type: str
    entity_id: str
    issue_type: str
    expected_detection: bool
    expected_decision: str
    severity: str
    rule_id: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def inject_anomalies_and_build_ground_truth(
    dataset: GeneratedDataset,
    id_gen: DeterministicIDGenerator,
    config: SystemConfig,
) -> tuple[GeneratedDataset, list[GroundTruthRecord]]:
    """Inject controlled anomalies into dedicated fixture rows and generate separate ground truth."""
    if not config.anomaly_injection_enabled:
        return dataset, []

    ground_truth: list[GroundTruthRecord] = []

    # 1. Anomaly: DUPLICATE_REVENUE
    # Pick a paid order and clone it with a new order_id but identical economic_transaction_key
    paid_orders = [o for o in dataset.orders if o["status"] == "PAID" and o["net_revenue"] > 0]
    if paid_orders:
        target_order = paid_orders[0]
        max_ord_idx = max(int(o["order_id"].split("-")[-1]) for o in dataset.orders)
        dup_order_id = f"ORD-2026-{max_ord_idx + 1:06d}"
        
        dup_order = {
            **target_order,
            "order_id": dup_order_id,
            "issue_type": "DUPLICATE_REVENUE",
        }
        dataset.orders.append(dup_order)

        gt1 = GroundTruthRecord(
            ground_truth_id=id_gen.ground_truth_id(),
            entity_type="order",
            entity_id=dup_order_id,
            issue_type="DUPLICATE_REVENUE",
            expected_detection=True,
            expected_decision="COUNT_ONCE_FLAG_DUPLICATE",
            severity="CRITICAL",
            rule_id="RULE-DUP-REV-01",
            notes=f"Duplicate order record sharing economic_transaction_key {target_order['economic_transaction_key']} with {target_order['order_id']}",
        )
        ground_truth.append(gt1)

    # 2. Anomaly: POST_CONVERSION_TOUCH
    # Add a touchpoint occurring 2 days AFTER an order conversion
    if paid_orders:
        target_order = paid_orders[min(1, len(paid_orders) - 1)]
        order_dt = datetime.fromisoformat(target_order["ordered_at"])
        post_touch_dt = order_dt + timedelta(days=2)
        
        # Scoped counter for this contact
        contact_id = target_order["contact_id"]
        contact_touches = [t for t in dataset.touchpoints if t.get("contact_id") == contact_id]
        max_tp_idx = len(contact_touches) + 1
        post_tid = f"TOUCH-{contact_id}-{max_tp_idx:06d}"

        cmp_id = dataset.campaigns[0]["campaign_id"]
        ch_id = dataset.campaigns[0]["channel_id"]

        post_touch = {
            "touchpoint_id": post_tid,
            "contact_id": contact_id,
            "campaign_id": cmp_id,
            "channel_id": ch_id,
            "creative_id": None,
            "occurred_at": post_touch_dt.isoformat(),
            "touch_type": "CLICK",
            "touch_mode": "ONLINE",
            "source_event_id": f"EVT-{post_tid}",
            "identity_evidence": "AUTHENTICATED",
            "issue_type": "POST_CONVERSION_TOUCH",
            "is_synthetic": True,
        }
        dataset.touchpoints.append(post_touch)

        gt2 = GroundTruthRecord(
            ground_truth_id=id_gen.ground_truth_id(),
            entity_type="touchpoint",
            entity_id=post_tid,
            issue_type="POST_CONVERSION_TOUCH",
            expected_detection=True,
            expected_decision="EXCLUDE_FROM_ATTRIBUTION",
            severity="MEDIUM",
            rule_id="RULE-TEMP-TOUCH-01",
            notes=f"Touchpoint occurred after conversion order {target_order['order_id']}",
        )
        ground_truth.append(gt2)

    # 3. Anomaly: CURRENCY_MISMATCH
    # Create a cost record in foreign currency with missing/None exchange rate
    if dataset.campaigns:
        target_cmp = dataset.campaigns[0]
        max_cost_idx = max(int(c["cost_record_id"].split("-")[-1]) for c in dataset.cost_records)
        curr_cost_id = f"COST-2026-{max_cost_idx + 1:06d}"

        curr_mismatch_cost = {
            "cost_record_id": curr_cost_id,
            "campaign_id": target_cmp["campaign_id"],
            "incurred_at": target_cmp["start_at"],
            "cost_type": "MEDIA",
            "amount": 2500.00,
            "currency": "EUR",
            "exchange_rate_to_reporting": None,  # Missing FX rate
            "reporting_amount": None,
            "rate_date": None,
            "source_reference": f"INV-{curr_cost_id}",
            "issue_type": "CURRENCY_MISMATCH",
        }
        dataset.cost_records.append(curr_mismatch_cost)

        gt3 = GroundTruthRecord(
            ground_truth_id=id_gen.ground_truth_id(),
            entity_type="cost_record",
            entity_id=curr_cost_id,
            issue_type="CURRENCY_MISMATCH",
            expected_detection=True,
            expected_decision="BLOCK_ROI_FLAG_UNRESOLVED_FX",
            severity="HIGH",
            rule_id="RULE-FX-RATE-01",
            notes="Cost record in EUR without valid exchange rate to reporting currency",
        )
        ground_truth.append(gt3)

    # 4. Anomaly: MISSING_CAMPAIGN_COST
    # Designate an active campaign with zero cost coverage
    active_cmps = [c for c in dataset.campaigns if c["status"] == "ACTIVE"]
    if active_cmps:
        missing_cmp = active_cmps[-1]
        missing_cmp_id = missing_cmp["campaign_id"]
        # Remove any existing cost records for this campaign
        dataset.cost_records = [c for c in dataset.cost_records if c["campaign_id"] != missing_cmp_id]

        gt4 = GroundTruthRecord(
            ground_truth_id=id_gen.ground_truth_id(),
            entity_type="campaign",
            entity_id=missing_cmp_id,
            issue_type="MISSING_CAMPAIGN_COST",
            expected_detection=True,
            expected_decision="MARK_INCOMPLETE_COST_ROI_UNAVAILABLE",
            severity="HIGH",
            rule_id="RULE-COST-COV-01",
            notes=f"Active campaign {missing_cmp_id} has zero recorded costs",
        )
        ground_truth.append(gt4)

    # 5. Anomaly: UNSUPPORTED_IDENTITY_LINK
    # Create an anonymous session with a contact link but identity_evidence = 'NONE'
    if dataset.contacts:
        target_contact = dataset.contacts[0]
        max_sess_idx = max(int(s["session_id"].split("-")[-1]) for s in dataset.web_sessions)
        anon_sess_id = f"SES-2026-{max_sess_idx + 1:06d}"
        base_dt = datetime.fromisoformat(target_contact["created_at"])

        unsupported_session = {
            "session_id": anon_sess_id,
            "contact_id": target_contact["contact_id"],
            "campaign_id": dataset.campaigns[0]["campaign_id"],
            "started_at": base_dt.isoformat(),
            "ended_at": (base_dt + timedelta(minutes=15)).isoformat(),
            "source_channel_id": dataset.channels[0]["channel_id"],
            "landing_path": "/pricing",
            "identity_evidence": "NONE",  # Unsupported evidence
            "is_anonymous": True,
            "issue_type": "UNSUPPORTED_IDENTITY_LINK",
        }
        dataset.web_sessions.append(unsupported_session)

        gt5 = GroundTruthRecord(
            ground_truth_id=id_gen.ground_truth_id(),
            entity_type="web_session",
            entity_id=anon_sess_id,
            issue_type="UNSUPPORTED_IDENTITY_LINK",
            expected_detection=True,
            expected_decision="QUARANTINE_IDENTITY_LINK",
            severity="MEDIUM",
            rule_id="RULE-ID-EVID-01",
            notes="Anonymous web session linked to contact without verified identity evidence",
        )
        ground_truth.append(gt5)

    return dataset, ground_truth


def export_ground_truth(ground_truth: list[GroundTruthRecord], output_path: Path | str) -> Path:
    """Save ground-truth cases to isolated CSV file."""
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not ground_truth:
        p.write_text("", encoding="utf-8")
        return p

    fieldnames = list(asdict(ground_truth[0]).keys())
    with open(p, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for gt in ground_truth:
            writer.writerow(gt.to_dict())
    return p
