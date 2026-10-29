"""Campaigns and ROI routes."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from src.attribution.api.schemas import (
    CampaignListResponse,
    CampaignDetailResponse,
    CampaignROIResponse,
)
from src.attribution.services.campaigns import CampaignService

router = APIRouter(prefix="/api/campaigns", tags=["Campaigns & ROI"])
service = CampaignService()


@router.get("", response_model=CampaignListResponse)
def list_campaigns(
    channel_id: Optional[str] = Query(None, description="Filter by channel ID"),
    status: Optional[str] = Query(None, description="Filter by status (ACTIVE, PAUSED, COMPLETED)"),
    search: Optional[str] = Query(None, description="Search by campaign name"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
) -> CampaignListResponse:
    c_id = channel_id if isinstance(channel_id, str) else None
    st = status if isinstance(status, str) else None
    srch = search if isinstance(search, str) else None
    p = page if isinstance(page, int) else 1
    ps = page_size if isinstance(page_size, int) else 20

    res = service.list_campaigns(
        channel_id=c_id,
        status=st,
        search=srch,
        page=p,
        page_size=ps,
    )
    return CampaignListResponse(**res)


@router.get("/{campaign_id}", response_model=CampaignDetailResponse)
def get_campaign_detail(campaign_id: str) -> CampaignDetailResponse:
    camp = service.get_campaign_detail(campaign_id)
    if not camp:
        raise HTTPException(status_code=404, detail=f"Campaign '{campaign_id}' not found.")
    return CampaignDetailResponse(**camp)


@router.get("/{campaign_id}/roi", response_model=CampaignROIResponse)
def get_campaign_roi(campaign_id: str) -> CampaignROIResponse:
    roi = service.get_campaign_roi(campaign_id)
    if not roi:
        raise HTTPException(status_code=404, detail=f"Campaign '{campaign_id}' not found.")
    return CampaignROIResponse(**roi)
