"""Attribution comparison and Order attribution routes."""

from datetime import date
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from src.attribution.api.schemas import (
    AttributionComparisonResponse,
    OrderAttributionResponse,
)
from src.attribution.services.attribution import AttributionService

router = APIRouter(tags=["Attribution"])
service = AttributionService()


@router.get("/api/attribution/compare", response_model=AttributionComparisonResponse)
def compare_attribution(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
) -> AttributionComparisonResponse:
    s_date = start_date if isinstance(start_date, date) else None
    e_date = end_date if isinstance(end_date, date) else None
    res = service.compare_attribution(start_date=s_date, end_date=e_date)
    return AttributionComparisonResponse(**res)


@router.get("/api/orders/{order_id}/attribution", response_model=OrderAttributionResponse)
def get_order_attribution(order_id: str) -> OrderAttributionResponse:
    res = service.get_order_attribution(order_id)
    if not res:
        raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found.")
    return OrderAttributionResponse(**res)


@router.get("/api/attribution/orders/{order_id}", response_model=OrderAttributionResponse)
def get_order_attribution_alias(order_id: str) -> OrderAttributionResponse:
    """Alias for /api/orders/{order_id}/attribution."""
    return get_order_attribution(order_id)
