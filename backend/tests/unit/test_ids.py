"""Unit tests for deterministic ID generation and validation."""

import pytest
from src.attribution.ids import (
    DeterministicIDGenerator,
    is_valid_campaign_id,
    is_valid_contact_id,
    is_valid_touchpoint_id,
    is_valid_session_id,
    is_valid_lead_id,
    is_valid_opportunity_id,
    is_valid_order_id,
    is_valid_cost_id,
    is_valid_channel_id,
    is_valid_creative_id,
    is_valid_audience_id,
)


def test_id_generator_monotonic_sequence():
    gen = DeterministicIDGenerator(year=2026)
    
    # Campaign IDs
    c1 = gen.campaign_id()
    c2 = gen.campaign_id()
    assert c1 == "CMP-2026-000001"
    assert c2 == "CMP-2026-000002"
    assert is_valid_campaign_id(c1)
    assert is_valid_campaign_id(c2)

    # Contact IDs
    con1 = gen.contact_id()
    assert con1 == "CON-000001"
    assert is_valid_contact_id(con1)

    # Scoped Touchpoints per contact
    t1_con1 = gen.touchpoint_id(contact_id=con1)
    t2_con1 = gen.touchpoint_id(contact_id=con1)
    assert t1_con1 == "TOUCH-CON-000001-000001"
    assert t2_con1 == "TOUCH-CON-000001-000002"
    assert is_valid_touchpoint_id(t1_con1)
    assert is_valid_touchpoint_id(t2_con1)

    # Anonymous Touchpoint
    t_anon = gen.touchpoint_id(contact_id=None)
    assert t_anon == "TOUCH-ANON-000001"
    assert is_valid_touchpoint_id(t_anon)

    # Session, Lead, Opp, Order, Cost
    s1 = gen.session_id()
    l1 = gen.lead_id()
    o1 = gen.opportunity_id()
    ord1 = gen.order_id()
    cost1 = gen.cost_id()

    assert s1 == "SES-2026-000001"
    assert l1 == "LEAD-2026-000001"
    assert o1 == "OPP-2026-000001"
    assert ord1 == "ORD-2026-000001"
    assert cost1 == "COST-2026-000001"

    assert is_valid_session_id(s1)
    assert is_valid_lead_id(l1)
    assert is_valid_opportunity_id(o1)
    assert is_valid_order_id(ord1)
    assert is_valid_cost_id(cost1)

    # Channels, Creatives, Audiences
    ch1 = gen.channel_id()
    cre1 = gen.creative_id()
    aud1 = gen.audience_id()

    assert ch1 == "CH-000001"
    assert cre1 == "CRE-000001"
    assert aud1 == "AUD-000001"

    assert is_valid_channel_id(ch1)
    assert is_valid_creative_id(cre1)
    assert is_valid_audience_id(aud1)


def test_id_generator_reset():
    gen = DeterministicIDGenerator(year=2026)
    assert gen.campaign_id() == "CMP-2026-000001"
    assert gen.contact_id() == "CON-000001"
    
    gen.reset()
    assert gen.campaign_id() == "CMP-2026-000001"
    assert gen.contact_id() == "CON-000001"


def test_invalid_ids():
    assert not is_valid_campaign_id("CMP-2025-001")
    assert not is_valid_campaign_id("CMP-2026-abc")
    assert not is_valid_contact_id("CONTACT-000001")
    assert not is_valid_touchpoint_id("TOUCH-12345")
    assert not is_valid_order_id("ORDER-000001")

