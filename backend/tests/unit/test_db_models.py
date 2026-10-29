"""Unit tests for SQLAlchemy ORM models and schema initialization."""

from datetime import datetime, timezone
from decimal import Decimal
import pytest
from sqlalchemy import select
from src.attribution.db.models import (
    Base,
    Campaign,
    Channel,
    Contact,
    CostRecord,
    Lead,
    Opportunity,
    Order,
    Touchpoint,
)
from src.attribution.db.session import create_db_engine, get_session_factory, init_db


@pytest.fixture
def db_session():
    """In-memory SQLite engine and session fixture."""
    engine = create_db_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = get_session_factory(engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def test_schema_init_and_relationship_flow(db_session):
    now = datetime.now(timezone.utc)

    # 1. Master Channel
    channel = Channel(
        channel_id="CH-000001",
        name="Google Search",
        channel_type="PAID_SEARCH",
        is_active=True,
        created_at=now,
    )
    db_session.add(channel)

    # 2. Master Campaign
    campaign = Campaign(
        campaign_id="CMP-2026-000001",
        name="Q1 Search Brand",
        channel_id="CH-000001",
        budget_amount=Decimal("50000.00"),
        currency="INR",
        start_at=now,
        end_at=now,
        status="ACTIVE",
        objective="AWARENESS",
        created_at=now,
    )
    db_session.add(campaign)

    # 3. Contact
    contact = Contact(
        contact_id="CON-000001",
        created_at=now,
        region="APAC",
        customer_segment="ENTERPRISE",
        consent_status="GRANTED",
        is_synthetic=True,
        identity_status="KNOWN",
    )
    db_session.add(contact)
    db_session.commit()

    # 4. Touchpoint
    touchpoint = Touchpoint(
        touchpoint_id="TOUCH-CON-000001-000001",
        contact_id="CON-000001",
        campaign_id="CMP-2026-000001",
        channel_id="CH-000001",
        occurred_at=now,
        touch_type="CLICK",
        touch_mode="ONLINE",
        identity_evidence="AUTHENTICATED",
        is_synthetic=True,
    )
    db_session.add(touchpoint)

    # 5. Lead
    lead = Lead(
        lead_id="LEAD-2026-000001",
        contact_id="CON-000001",
        created_at=now,
        status="QUALIFIED",
        source_type="WEB",
    )
    db_session.add(lead)

    # 6. Opportunity
    opp = Opportunity(
        opportunity_id="OPP-2026-000001",
        lead_id="LEAD-2026-000001",
        created_at=now,
        expected_value=Decimal("15000.00"),
        currency="INR",
        status="WON",
        closed_at=now,
        actual_closed_value=Decimal("15000.00"),
    )
    db_session.add(opp)

    # 7. Order
    order = Order(
        order_id="ORD-2026-000001",
        opportunity_id="OPP-2026-000001",
        contact_id="CON-000001",
        ordered_at=now,
        status="PAID",
        gross_amount=Decimal("15000.00"),
        refund_amount=Decimal("0.00"),
        net_revenue=Decimal("15000.00"),
        currency="INR",
        economic_transaction_key="TXN-2026-000001",
    )
    db_session.add(order)

    # 8. Cost Record
    cost = CostRecord(
        cost_record_id="COST-2026-000001",
        campaign_id="CMP-2026-000001",
        incurred_at=now,
        cost_type="MEDIA",
        amount=Decimal("3500.00"),
        currency="INR",
        reporting_amount=Decimal("3500.00"),
    )
    db_session.add(cost)
    db_session.commit()

    # Assert relations
    queried_campaign = db_session.scalar(select(Campaign).where(Campaign.campaign_id == "CMP-2026-000001"))
    assert queried_campaign is not None
    assert queried_campaign.channel.name == "Google Search"
    assert len(queried_campaign.touchpoints) == 1
    assert queried_campaign.touchpoints[0].touchpoint_id == "TOUCH-CON-000001-000001"

    queried_order = db_session.scalar(select(Order).where(Order.order_id == "ORD-2026-000001"))
    assert queried_order is not None
    assert queried_order.contact.contact_id == "CON-000001"
    assert queried_order.net_revenue == Decimal("15000.00")

