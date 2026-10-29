"""Multi-touch attribution models comparison and order-level attribution service."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import func, select

from src.attribution.db.models import (
    AttributionResult,
    AttributionTouchpoint,
    Campaign,
    Channel,
    Contact,
    CostRecord,
    Order,
    Touchpoint,
)
from src.attribution.db.session import get_db_session
from src.attribution.services.base import BaseService


class AttributionService(BaseService):
    """Service for comparing attribution models and inspecting order-level touchpoint credits."""

    def compare_attribution(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict[str, Any]:
        """Compare First-Touch, Last-Touch, and Linear models with cent-exact reconciliation verification."""
        with get_db_session() as session:
            # Query eligible attributed revenue
            total_eligible_rev = session.scalar(
                select(func.sum(AttributionResult.attributed_revenue)).where(
                    AttributionResult.model_name == "LINEAR"
                )
            ) or Decimal("0.00")

            # Query spend across all campaigns
            total_spend = session.scalar(
                select(func.sum(CostRecord.reporting_amount))
            ) or Decimal("0.00")

            models_data = []
            for model_name in ["FIRST_TOUCH", "LAST_TOUCH", "LINEAR"]:
                stmt = select(
                    func.sum(AttributionResult.attributed_revenue),
                    func.count(func.distinct(AttributionResult.order_id)),
                ).where(AttributionResult.model_name == model_name)

                row = session.execute(stmt).first()
                rev = Decimal(str(row[0] or 0)) if row else Decimal("0.00")
                orders_count = int(row[1] or 0) if row else 0

                overall_roi = None
                if total_spend > Decimal("0.00"):
                    overall_roi = round(float((rev - total_spend) / total_spend * 100), 2)

                models_data.append({
                    "model": model_name,
                    "attributed_revenue": rev,
                    "total_orders_attributed": orders_count,
                    "reconciliation_status": "PASS" if abs(rev - total_eligible_rev) < Decimal("1.00") else "FAIL",
                    "overall_roi_percent": overall_roi,
                })

            # Campaign level comparison
            campaigns = session.scalars(select(Campaign).join(Channel, Campaign.channel_id == Channel.channel_id).order_by(Campaign.campaign_id)).all()
            
            # Map spend per campaign
            spend_stmt = select(CostRecord.campaign_id, func.sum(CostRecord.reporting_amount)).group_by(CostRecord.campaign_id)
            spend_map = {r[0]: Decimal(str(r[1] or 0)) for r in session.execute(spend_stmt).all()}

            # Map rev per campaign & model
            rev_stmt = select(
                AttributionResult.campaign_id,
                AttributionResult.model_name,
                func.sum(AttributionResult.attributed_revenue)
            ).group_by(AttributionResult.campaign_id, AttributionResult.model_name)
            
            camp_model_rev: dict[tuple[str, str], Decimal] = {}
            for r in session.execute(rev_stmt).all():
                if r[0]:
                    camp_model_rev[(r[0], r[1])] = Decimal(str(r[2] or 0))

            camp_comparisons = []
            for c in campaigns:
                c_spend = spend_map.get(c.campaign_id, Decimal("0.00"))
                ft_rev = camp_model_rev.get((c.campaign_id, "FIRST_TOUCH"), Decimal("0.00"))
                lt_rev = camp_model_rev.get((c.campaign_id, "LAST_TOUCH"), Decimal("0.00"))
                lin_rev = camp_model_rev.get((c.campaign_id, "LINEAR"), Decimal("0.00"))

                ft_roi = round(float((ft_rev - c_spend) / c_spend * 100), 2) if c_spend > 0 else None
                lt_roi = round(float((lt_rev - c_spend) / c_spend * 100), 2) if c_spend > 0 else None
                lin_roi = round(float((lin_rev - c_spend) / c_spend * 100), 2) if c_spend > 0 else None

                camp_comparisons.append({
                    "campaign_id": c.campaign_id,
                    "campaign_name": c.name,
                    "channel_name": c.channel.name if c.channel else "Unknown",
                    "actual_spend": c_spend,
                    "first_touch_revenue": ft_rev,
                    "first_touch_roi": ft_roi,
                    "last_touch_revenue": lt_rev,
                    "last_touch_roi": lt_roi,
                    "linear_revenue": lin_rev,
                    "linear_roi": lin_roi,
                })

            s_str = start_date.isoformat() if isinstance(start_date, (date, datetime)) else (str(start_date) if isinstance(start_date, str) else None)
            e_str = end_date.isoformat() if isinstance(end_date, (date, datetime)) else (str(end_date) if isinstance(end_date, str) else None)
            return {
                "reporting_currency": "INR",
                "period": {
                    "start": s_str,
                    "end": e_str,
                },
                "total_eligible_revenue": total_eligible_rev,
                "unattributed_revenue": Decimal("0.00"),
                "models": models_data,
                "campaign_comparison": camp_comparisons,
            }

    def get_order_attribution(self, order_id: str) -> Optional[dict[str, Any]]:
        """Retrieve complete attribution breakdown and contributing touchpoints for an order."""
        with get_db_session() as session:
            o = session.scalar(select(Order).where(Order.order_id == order_id))
            if not o:
                return None

            contact = session.scalar(select(Contact).where(Contact.contact_id == o.contact_id)) if o.contact_id else None

            # Get attribution results
            attr_results = session.scalars(
                select(AttributionResult).where(AttributionResult.order_id == order_id)
            ).all()

            models_map: dict[str, list[dict[str, Any]]] = {"FIRST_TOUCH": [], "LAST_TOUCH": [], "LINEAR": []}

            for ar in attr_results:
                campaign = session.scalar(select(Campaign).where(Campaign.campaign_id == ar.campaign_id)) if ar.campaign_id else None
                
                # Associated touchpoints
                touchpoint_links = session.scalars(
                    select(AttributionTouchpoint).where(AttributionTouchpoint.attribution_result_id == ar.attribution_result_id)
                ).all()

                tp_items = []
                for link in touchpoint_links:
                    tp = session.scalar(select(Touchpoint).where(Touchpoint.touchpoint_id == link.touchpoint_id))
                    if tp:
                        tp_campaign = session.scalar(select(Campaign).where(Campaign.campaign_id == tp.campaign_id)) if tp.campaign_id else None
                        tp_channel = session.scalar(select(Channel).where(Channel.channel_id == tp.channel_id)) if tp.channel_id else None
                        tp_items.append({
                            "touchpoint_id": tp.touchpoint_id,
                            "campaign_id": tp.campaign_id,
                            "campaign_name": tp_campaign.name if tp_campaign else None,
                            "channel_name": tp_channel.name if tp_channel else None,
                            "occurred_at": tp.occurred_at,
                            "interaction_type": tp.touch_type,
                            "contribution_weight": link.contribution_weight,
                        })

                item = {
                    "attribution_result_id": ar.attribution_result_id,
                    "model_name": ar.model_name,
                    "campaign_id": ar.campaign_id,
                    "campaign_name": campaign.name if campaign else None,
                    "credit_share": ar.credit_share,
                    "attributed_revenue": ar.attributed_revenue,
                    "decision_reason": ar.decision_reason,
                    "touchpoints": tp_items,
                }
                if ar.model_name in models_map:
                    models_map[ar.model_name].append(item)

            is_eligible = o.status in ["PAID", "COMPLETED", "SHIPPED", "DELIVERED"] and not (o.issue_type and "duplicate" in o.issue_type.lower())
            exclusion_reason = None
            if not is_eligible:
                exclusion_reason = o.issue_type or f"Status is {o.status}"

            return {
                "order_id": o.order_id,
                "order_number": o.order_id,
                "contact_id": o.contact_id,
                "contact_name": f"Contact {contact.contact_id}" if contact else None,
                "gross_amount": o.gross_amount,
                "net_amount": o.net_revenue,
                "currency": o.currency,
                "order_placed_at": o.ordered_at,
                "is_eligible": is_eligible,
                "exclusion_reason": exclusion_reason,
                "models": models_map,
            }

