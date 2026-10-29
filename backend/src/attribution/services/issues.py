"""Data quality issues and exception detection inspection service."""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import desc, func, select

from src.attribution.db.models import Campaign, DataIssue, Order, Touchpoint
from src.attribution.db.session import get_db_session
from src.attribution.services.base import BaseService


class IssueService(BaseService):
    """Service for querying detected data anomalies, mitigation decisions, and affected entity links."""

    def list_issues(
        self,
        issue_type: Optional[str] = None,
        severity: Optional[str] = None,
        resolution_status: Optional[str] = None,
        entity_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """List filterable data quality issues and automated mitigation decisions."""
        with get_db_session() as session:
            stmt = select(DataIssue)
            if issue_type:
                stmt = stmt.where(DataIssue.issue_type == issue_type)
            if severity:
                stmt = stmt.where(DataIssue.severity == severity)
            if resolution_status:
                stmt = stmt.where(DataIssue.resolution_status == resolution_status)
            if entity_type:
                stmt = stmt.where(DataIssue.entity_type == entity_type)

            total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
            issues = session.scalars(stmt.order_by(desc(DataIssue.detected_at)).offset((page - 1) * page_size).limit(page_size)).all()

            return {
                "total": total,
                "page": page,
                "page_size": page_size,
                "issues": [
                    {
                        "issue_id": iss.issue_id,
                        "entity_type": iss.entity_type,
                        "entity_id": iss.entity_id,
                        "issue_type": iss.issue_type,
                        "severity": iss.severity,
                        "detected_at": iss.detected_at,
                        "decision": iss.decision,
                        "resolution_status": iss.resolution_status,
                    }
                    for iss in issues
                ],
            }

    def get_issue_detail(self, issue_id: str) -> Optional[dict[str, Any]]:
        """Retrieve complete exception context, payload details, and linked entity records."""
        with get_db_session() as session:
            iss = session.scalar(select(DataIssue).where(DataIssue.issue_id == issue_id))
            if not iss:
                return None

            # Fetch related records if applicable
            related = []
            if iss.entity_type == "order":
                ord_row = session.scalar(select(Order).where(Order.order_id == iss.entity_id))
                if ord_row:
                    related.append({"type": "order", "id": ord_row.order_id, "amount": str(ord_row.gross_amount), "status": ord_row.status})
            elif iss.entity_type == "touchpoint":
                tp_row = session.scalar(select(Touchpoint).where(Touchpoint.touchpoint_id == iss.entity_id))
                if tp_row:
                    related.append({"type": "touchpoint", "id": tp_row.touchpoint_id, "interaction_type": tp_row.touch_type, "occurred_at": tp_row.occurred_at.isoformat()})
            elif iss.entity_type == "campaign":
                c_row = session.scalar(select(Campaign).where(Campaign.campaign_id == iss.entity_id))
                if c_row:
                    related.append({"type": "campaign", "id": c_row.campaign_id, "name": c_row.name, "budget": str(c_row.budget_amount)})

            return {
                "issue_id": iss.issue_id,
                "run_id": iss.run_id,
                "entity_type": iss.entity_type,
                "entity_id": iss.entity_id,
                "issue_type": iss.issue_type,
                "severity": iss.severity,
                "detected_at": iss.detected_at,
                "decision": iss.decision,
                "resolution_status": iss.resolution_status,
                "details": iss.details_json,
                "related_records": related,
            }

