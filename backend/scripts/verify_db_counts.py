"""Verify and display all table row counts in the connected database."""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import func, select
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
from src.attribution.db.session import get_db_session


def main() -> None:
    models = [
        Channel,
        Creative,
        Audience,
        Campaign,
        CampaignCreative,
        CampaignAudience,
        Contact,
        Touchpoint,
        WebSession,
        Lead,
        Opportunity,
        OpportunityEvent,
        Order,
        OrderEvent,
        CostRecord,
        PipelineRun,
        AttributionResult,
        AttributionTouchpoint,
        DataIssue,
        ValidationResult,
    ]

    print("=========================================")
    print("PostgreSQL Database Table Row Counts")
    print("=========================================")
    print(f"{'Table Name':<25} {'Row Count':>12}")
    print("-----------------------------------------")

    with get_db_session() as session:
        for model in models:
            cnt = session.scalar(select(func.count()).select_from(model))
            print(f"{model.__tablename__:<25} {cnt:>12,}")

    print("=========================================")


if __name__ == "__main__":
    main()

