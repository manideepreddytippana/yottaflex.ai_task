"""Pydantic schemas for the Marketing Attribution REST API."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"
    database_connected: bool = True
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Runs & Validation
# ---------------------------------------------------------------------------
class RunSummary(BaseModel):
    run_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    seed: int
    generator_version: str
    dataset_scale: str
    total_entities: int = 0


class RunDetailResponse(BaseModel):
    run_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    seed: int
    generator_version: str
    config_hash: str
    dataset_scale: str
    row_counts: dict[str, int] = Field(default_factory=dict)
    checksums: dict[str, str] = Field(default_factory=dict)


class RunCreateRequest(BaseModel):
    scale: str = Field("starter", description="'starter' or 'full'")
    seed: int = Field(20261022, description="Random seed")


class ValidationSummaryResponse(BaseModel):
    run_id: str
    overall_status: str
    total_checks: int
    passed_checks: int
    failed_checks: int
    checks: list[dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Campaigns & ROI
# ---------------------------------------------------------------------------
class CampaignListItem(BaseModel):
    campaign_id: str
    name: str
    channel_id: str
    channel_name: Optional[str] = None
    status: str
    budget_amount: Decimal
    actual_spend: Decimal = Decimal("0.00")
    spend_coverage_status: str = "COMPLETE"
    attributed_revenue_linear: Decimal = Decimal("0.00")
    roi_percent_linear: Optional[float] = None
    start_at: datetime
    end_at: datetime


class CampaignListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    campaigns: list[CampaignListItem]


class CampaignDetailResponse(BaseModel):
    campaign_id: str
    name: str
    channel_id: str
    channel_name: Optional[str] = None
    status: str
    objective: Optional[str] = None
    budget_amount: Decimal
    currency: str
    start_at: datetime
    end_at: datetime
    actual_spend: Decimal
    spend_coverage_status: str
    creatives: list[dict[str, Any]] = Field(default_factory=list)
    audiences: list[dict[str, Any]] = Field(default_factory=list)
    first_touch_revenue: Decimal = Decimal("0.00")
    last_touch_revenue: Decimal = Decimal("0.00")
    linear_revenue: Decimal = Decimal("0.00")
    first_touch_roi: Optional[float] = None
    last_touch_roi: Optional[float] = None
    linear_roi: Optional[float] = None


class CampaignROIResponse(BaseModel):
    campaign_id: str
    campaign_name: str
    actual_spend: Decimal
    spend_coverage_status: str
    reporting_currency: str = "INR"
    first_touch: dict[str, Any]
    last_touch: dict[str, Any]
    linear: dict[str, Any]
    reconciliation_status: str = "PASS"


# ---------------------------------------------------------------------------
# Attribution Comparison
# ---------------------------------------------------------------------------
class AttributionModelSummary(BaseModel):
    model: str
    attributed_revenue: Decimal
    total_orders_attributed: int
    reconciliation_status: str
    overall_roi_percent: Optional[float] = None


class CampaignAttributionComparison(BaseModel):
    campaign_id: str
    campaign_name: str
    channel_name: str
    actual_spend: Decimal
    first_touch_revenue: Decimal
    first_touch_roi: Optional[float] = None
    last_touch_revenue: Decimal
    last_touch_roi: Optional[float] = None
    linear_revenue: Decimal
    linear_roi: Optional[float] = None


class AttributionComparisonResponse(BaseModel):
    reporting_currency: str = "INR"
    period: dict[str, Optional[str]]
    total_eligible_revenue: Decimal
    unattributed_revenue: Decimal = Decimal("0.00")
    models: list[AttributionModelSummary]
    campaign_comparison: list[CampaignAttributionComparison] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Order Attribution
# ---------------------------------------------------------------------------
class TouchpointContributionItem(BaseModel):
    touchpoint_id: str
    campaign_id: Optional[str] = None
    campaign_name: Optional[str] = None
    channel_name: Optional[str] = None
    occurred_at: datetime
    interaction_type: str
    contribution_weight: Decimal


class AttributionResultItem(BaseModel):
    attribution_result_id: str
    model_name: str
    campaign_id: Optional[str] = None
    campaign_name: Optional[str] = None
    credit_share: Decimal
    attributed_revenue: Decimal
    decision_reason: Optional[str] = None
    touchpoints: list[TouchpointContributionItem] = Field(default_factory=list)


class OrderAttributionResponse(BaseModel):
    order_id: str
    order_number: str
    contact_id: str
    contact_name: Optional[str] = None
    gross_amount: Decimal
    net_amount: Decimal
    currency: str
    order_placed_at: datetime
    is_eligible: bool = True
    exclusion_reason: Optional[str] = None
    models: dict[str, list[AttributionResultItem]] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Customer Journey Explorer
# ---------------------------------------------------------------------------
class JourneyTimelineItem(BaseModel):
    event_id: str
    event_type: str  # touchpoint, session, lead, opportunity, order, event
    occurred_at: datetime
    title: str
    details: dict[str, Any] = Field(default_factory=dict)
    is_eligible_touch: Optional[bool] = None
    exclusion_reason: Optional[str] = None


class CustomerJourneyResponse(BaseModel):
    contact_id: str
    full_name: str
    email: str
    lifecycle_stage: str
    total_touchpoints: int
    total_orders: int
    total_spend_attributed: Decimal = Decimal("0.00")
    timeline: list[JourneyTimelineItem] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Exceptions & Data Quality
# ---------------------------------------------------------------------------
class DataIssueListItem(BaseModel):
    issue_id: str
    entity_type: str
    entity_id: str
    issue_type: str
    severity: str
    detected_at: datetime
    decision: Optional[str] = None
    resolution_status: str


class DataIssueListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    issues: list[DataIssueListItem]


class DataIssueDetailResponse(BaseModel):
    issue_id: str
    run_id: Optional[str] = None
    entity_type: str
    entity_id: str
    issue_type: str
    severity: str
    detected_at: datetime
    decision: Optional[str] = None
    resolution_status: str
    details: Optional[dict[str, Any]] = None
    related_records: list[dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Evaluation Metrics
# ---------------------------------------------------------------------------
class EvaluationMetricsResponse(BaseModel):
    precision: float
    recall: float
    f1_score: float
    true_positives: int
    false_positives: int
    false_negatives: int
    attribution_coverage_percent: float
    roi_availability_percent: float
    reconciliation_pass_rate_percent: float
    scenarios_evaluated: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------
class ExportItem(BaseModel):
    filename: str
    file_type: str  # csv, sql, json, sha256
    file_size_bytes: int
    checksum_sha256: Optional[str] = None
    relative_path: str


class RunExportsResponse(BaseModel):
    run_id: str
    output_dir: str
    exports: list[ExportItem]

