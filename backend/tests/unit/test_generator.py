"""Unit tests for the Deterministic Synthetic Data Generator."""

from datetime import datetime
from decimal import Decimal
from pathlib import Path
import pytest

from src.attribution.config import load_config
from src.attribution.export.checksums import generate_checksums_file, verify_checksums
from src.attribution.export.csv_export import export_dataset_to_csv
from src.attribution.generator.orchestrator import generate_dataset


@pytest.fixture
def starter_config():
    return load_config("config/starter.yaml")


def test_generator_deterministic_repeatability(starter_config):
    """Running generator with same seed must produce identical outputs."""
    ds1 = generate_dataset(starter_config)
    ds2 = generate_dataset(starter_config)

    assert ds1.get_row_counts() == ds2.get_row_counts()
    
    # Assert sample campaigns, contacts, touchpoints, and orders match exactly
    assert ds1.campaigns[0] == ds2.campaigns[0]
    assert ds1.contacts[0] == ds2.contacts[0]
    assert ds1.touchpoints[0] == ds2.touchpoints[0]
    assert ds1.orders[0] == ds2.orders[0]


def test_generator_target_counts(starter_config):
    """Generated dataset meets target count parameters."""
    ds = generate_dataset(starter_config)
    counts = ds.get_row_counts()

    assert counts["campaign"] == starter_config.counts.campaigns
    assert counts["contact"] == starter_config.counts.contacts
    assert counts["touchpoint"] == starter_config.counts.touchpoints
    assert counts["opportunity"] == starter_config.counts.opportunities
    assert counts["channel"] > 0
    assert counts["order"] > 0
    assert counts["cost_record"] > 0


def test_generator_referential_integrity(starter_config):
    """All foreign key references point to existing parents in generated records."""
    ds = generate_dataset(starter_config)

    channel_ids = {c["channel_id"] for c in ds.channels}
    campaign_ids = {c["campaign_id"] for c in ds.campaigns}
    contact_ids = {c["contact_id"] for c in ds.contacts}
    session_ids = {s["session_id"] for s in ds.web_sessions}
    lead_ids = {l["lead_id"] for l in ds.leads}
    opp_ids = {o["opportunity_id"] for o in ds.opportunities}

    # Campaigns reference channels
    for c in ds.campaigns:
        assert c["channel_id"] in channel_ids

    # Touchpoints reference channels, campaigns, contacts
    for t in ds.touchpoints:
        assert t["channel_id"] in channel_ids
        if t["campaign_id"]:
            assert t["campaign_id"] in campaign_ids
        if t["contact_id"]:
            assert t["contact_id"] in contact_ids

    # Web sessions reference contacts and campaigns
    for s in ds.web_sessions:
        if s["contact_id"]:
            assert s["contact_id"] in contact_ids
        if s["campaign_id"]:
            assert s["campaign_id"] in campaign_ids

    # Leads reference contacts and sessions
    for l in ds.leads:
        assert l["contact_id"] in contact_ids
        if l["session_id"]:
            assert l["session_id"] in session_ids

    # Opportunities reference leads
    for o in ds.opportunities:
        assert o["lead_id"] in lead_ids

    # Orders reference opportunities and contacts
    for o in ds.orders:
        if o["opportunity_id"]:
            assert o["opportunity_id"] in opp_ids
        assert o["contact_id"] in contact_ids

    # Cost records reference campaigns
    for c in ds.cost_records:
        assert c["campaign_id"] in campaign_ids


def test_generator_temporal_order(starter_config):
    """Temporal constraints must hold across all generated entities."""
    ds = generate_dataset(starter_config)

    for cmp in ds.campaigns:
        start = datetime.fromisoformat(cmp["start_at"])
        end = datetime.fromisoformat(cmp["end_at"])
        assert start <= end

    for sess in ds.web_sessions:
        if sess["ended_at"]:
            assert datetime.fromisoformat(sess["ended_at"]) >= datetime.fromisoformat(sess["started_at"])

    for opp in ds.opportunities:
        if opp["closed_at"]:
            assert datetime.fromisoformat(opp["closed_at"]) >= datetime.fromisoformat(opp["created_at"])


def test_generator_financial_invariants(starter_config):
    """Net revenue arithmetic and currency conversion rates."""
    ds = generate_dataset(starter_config)

    for o in ds.orders:
        gross = Decimal(str(o["gross_amount"]))
        refund = Decimal(str(o["refund_amount"]))
        net = Decimal(str(o["net_revenue"]))
        assert net == gross - refund
        assert net >= 0

    for c in ds.cost_records:
        assert c["amount"] >= 0
        expected_reporting = round(c["amount"] * c["exchange_rate_to_reporting"], 2)
        assert abs(c["reporting_amount"] - expected_reporting) < 0.05


def test_export_and_checksum_verification(starter_config, tmp_path):
    """Dataset export to CSV generates valid SHA-256 manifest."""
    ds = generate_dataset(starter_config)
    export_dataset_to_csv(ds, tmp_path)

    checksum_file = generate_checksums_file(tmp_path)
    assert checksum_file.is_file()

    valid, errors = verify_checksums(tmp_path)
    assert valid is True
    assert len(errors) == 0

