"""Integration test for database loading into in-memory SQLite and verification."""

from pathlib import Path
import pytest
from sqlalchemy import func, select

from scripts.load_data import load_dataset
from src.attribution.db.models import Campaign, Contact, Order, Touchpoint
from src.attribution.db.session import create_db_engine, get_session_factory


def test_db_loading_integration(tmp_path):
    data_dir = Path("data/generated/full") if Path("data/generated/full").is_dir() else Path("data/generated/starter")
    if not data_dir.is_dir() or not (data_dir / "campaign.csv").is_file():
        pytest.skip("Dataset not generated yet")

    test_db_path = tmp_path / "test_integration.db"
    db_url = f"sqlite:///{test_db_path.as_posix()}"

    loaded_counts = load_dataset(data_dir, db_url=db_url, clean=True)

    assert loaded_counts["campaign"] >= 25
    assert loaded_counts["contact"] >= 1000
    assert loaded_counts["touchpoint"] >= 4000
    assert loaded_counts["order"] > 0

    # Query loaded tables using SQLAlchemy
    engine = create_db_engine(db_url)
    session_factory = get_session_factory(engine)
    with session_factory() as session:
        cmp_count = session.scalar(select(func.count(Campaign.campaign_id)))
        assert cmp_count >= 25

        contact_count = session.scalar(select(func.count(Contact.contact_id)))
        assert contact_count >= 1000

        touch_count = session.scalar(select(func.count(Touchpoint.touchpoint_id)))
        assert touch_count >= 4000

        order_count = session.scalar(select(func.count(Order.order_id)))
        assert order_count == loaded_counts["order"]

