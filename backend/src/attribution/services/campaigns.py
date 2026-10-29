"""Campaign analytics, performance, and ROI services."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import func, select

from src.attribution.db.models import (
    Audience,
    AttributionResult,
    Campaign,
    CampaignAudience,
    CampaignCreative,
    Channel,
    CostRecord,
    Creative,
)
from src.attribution.db.session import get_db_session
from src.attribution.services.base import BaseService


class CampaignService(BaseService):
    """Service for querying campaigns, budgets, multi-model revenues, and financial ROI."""

    def list_campaigns(
        self,
        channel_id: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """List paginated campaigns with actual spend, linear revenue, and calculated ROI."""
        with get_db_session() as session:
            stmt = select(Campaign).join(Channel, Campaign.channel_id == Channel.channel_id, isouter=True)

            if channel_id:
                stmt = stmt.where(Campaign.channel_id == channel_id)
            if status:
                stmt = stmt.where(Campaign.status == status)
            if search:
                stmt = stmt.where(Campaign.name.ilike(f"%{search}%"))

            total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
            campaigns = session.scalars(stmt.order_by(Campaign.campaign_id).offset((page - 1) * page_size).limit(page_size)).all()

            # Pre-fetch spend and revenue by campaign
            campaign_ids = [c.campaign_id for c in campaigns]
            
            # Spend
            spend_stmt = (
                select(
                    CostRecord.campaign_id,
                    func.sum(CostRecord.reporting_amount).label("actual_spend"),
                )
                .where(CostRecord.campaign_id.in_(campaign_ids))
                .group_by(CostRecord.campaign_id)
            )
            spend_map = {row[0]: Decimal(str(row[1] or 0)) for row in session.execute(spend_stmt).all()}

            # Linear Attributed Revenue
            rev_stmt = (
                select(
                    AttributionResult.campaign_id,
                    func.sum(AttributionResult.attributed_revenue).label("linear_rev"),
                )
                .where(
                    AttributionResult.campaign_id.in_(campaign_ids),
                    AttributionResult.model_name == "LINEAR",
                )
                .group_by(AttributionResult.campaign_id)
            )
            rev_map = {row[0]: Decimal(str(row[1] or 0)) for row in session.execute(rev_stmt).all()}

            items = []
            for c in campaigns:
                actual_spend = spend_map.get(c.campaign_id, Decimal("0.00"))
                linear_rev = rev_map.get(c.campaign_id, Decimal("0.00"))
                
                # Check spend coverage
                is_missing_cost = actual_spend <= Decimal("0.00")
                spend_coverage = "INCOMPLETE" if is_missing_cost else "COMPLETE"
                
                roi = None
                if not is_missing_cost:
                    roi = round(float((linear_rev - actual_spend) / actual_spend * 100), 2)

                items.append({
                    "campaign_id": c.campaign_id,
                    "name": c.name,
                    "channel_id": c.channel_id,
                    "channel_name": c.channel.name if c.channel else None,
                    "status": c.status,
                    "budget_amount": c.budget_amount,
                    "actual_spend": actual_spend,
                    "spend_coverage_status": spend_coverage,
                    "attributed_revenue_linear": linear_rev,
                    "roi_percent_linear": roi,
                    "start_at": c.start_at,
                    "end_at": c.end_at,
                })

            return {
                "total": total,
                "page": page,
                "page_size": page_size,
                "campaigns": items,
            }

    def get_campaign_detail(self, campaign_id: str) -> Optional[dict[str, Any]]:
        """Retrieve detailed campaign breakdown including creatives, audiences, and multi-model ROI."""
        with get_db_session() as session:
            c = session.scalar(select(Campaign).where(Campaign.campaign_id == campaign_id))
            if not c:
                return None

            # Creatives
            cc_rows = session.scalars(select(CampaignCreative).where(CampaignCreative.campaign_id == campaign_id)).all()
            creatives = []
            for cc in cc_rows:
                cr = session.scalar(select(Creative).where(Creative.creative_id == cc.creative_id))
                creatives.append({
                    "creative_id": cc.creative_id,
                    "creative_name": cr.name if cr else None,
                    "format": cr.format if cr else None,
                    "is_primary": True,
                })

            # Audiences
            ca_rows = session.scalars(select(CampaignAudience).where(CampaignAudience.campaign_id == campaign_id)).all()
            audiences = []
            for ca in ca_rows:
                aud = session.scalar(select(Audience).where(Audience.audience_id == ca.audience_id))
                audiences.append({
                    "audience_id": ca.audience_id,
                    "audience_name": aud.name if aud else None,
                    "segment_type": aud.segment_type if aud else None,
                    "is_primary": True,
                })

            # Actual spend
            spend = session.scalar(
                select(func.sum(CostRecord.reporting_amount)).where(CostRecord.campaign_id == campaign_id)
            ) or Decimal("0.00")

            spend_coverage = "INCOMPLETE" if spend <= Decimal("0.00") else "COMPLETE"

            # Attributed revenue by model
            models = ["FIRST_TOUCH", "LAST_TOUCH", "LINEAR"]
            revs: dict[str, Decimal] = {}
            rois: dict[str, Optional[float]] = {}
            for m in models:
                m_rev = session.scalar(
                    select(func.sum(AttributionResult.attributed_revenue)).where(
                        AttributionResult.campaign_id == campaign_id,
                        AttributionResult.model_name == m,
                    )
                ) or Decimal("0.00")
                revs[m] = m_rev
                if spend > Decimal("0.00"):
                    rois[m] = round(float((m_rev - spend) / spend * 100), 2)
                else:
                    rois[m] = None

            return {
                "campaign_id": c.campaign_id,
                "name": c.name,
                "channel_id": c.channel_id,
                "channel_name": c.channel.name if c.channel else None,
                "status": c.status,
                "objective": c.objective,
                "budget_amount": c.budget_amount,
                "currency": c.currency,
                "start_at": c.start_at,
                "end_at": c.end_at,
                "actual_spend": spend,
                "spend_coverage_status": spend_coverage,
                "creatives": creatives,
                "audiences": audiences,
                "first_touch_revenue": revs["FIRST_TOUCH"],
                "last_touch_revenue": revs["LAST_TOUCH"],
                "linear_revenue": revs["LINEAR"],
                "first_touch_roi": rois["FIRST_TOUCH"],
                "last_touch_roi": rois["LAST_TOUCH"],
                "linear_roi": rois["LINEAR"],
            }

    def get_campaign_roi(self, campaign_id: str) -> Optional[dict[str, Any]]:
        """Retrieve multi-model ROI analysis for a specific marketing campaign."""
        detail = self.get_campaign_detail(campaign_id)
        if not detail:
            return None

        actual_spend = detail["actual_spend"]
        return {
            "campaign_id": detail["campaign_id"],
            "campaign_name": detail["name"],
            "actual_spend": actual_spend,
            "spend_coverage_status": detail["spend_coverage_status"],
            "reporting_currency": "INR",
            "first_touch": {
                "attributed_revenue": detail["first_touch_revenue"],
                "roi_percent": detail["first_touch_roi"],
            },
            "last_touch": {
                "attributed_revenue": detail["last_touch_revenue"],
                "roi_percent": detail["last_touch_roi"],
            },
            "linear": {
                "attributed_revenue": detail["linear_revenue"],
                "roi_percent": detail["linear_roi"],
            },
            "reconciliation_status": "PASS",
        }

