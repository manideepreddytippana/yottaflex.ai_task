"""SQLAlchemy 2.0 Declarative ORM Models for the Marketing Attribution System.

Implements all entities specified in Section 5 of implementation_plan.md:
- Master tables: Channel, Campaign, Creative, Audience, Contact
- Bridges: CampaignCreative, CampaignAudience, AttributionTouchpoint
- Funnel & Events: Touchpoint, WebSession, Lead, Opportunity, Order, CostRecord
- Attribution & Telemetry: AttributionResult, OpportunityEvent, OrderEvent,
  PipelineRun, DataIssue, ValidationResult
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    JSON,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


class Channel(Base):
    __tablename__ = "channel"

    channel_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    channel_type: Mapped[str] = mapped_column(String(30), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    campaigns: Mapped[list["Campaign"]] = relationship("Campaign", back_populates="channel")
    touchpoints: Mapped[list["Touchpoint"]] = relationship("Touchpoint", back_populates="channel")


class Campaign(Base):
    __tablename__ = "campaign"
    __table_args__ = (
        CheckConstraint("budget_amount >= 0", name="chk_campaign_budget"),
        CheckConstraint("start_at <= end_at", name="chk_campaign_dates"),
        Index("idx_campaign_channel", "channel_id"),
        Index("idx_campaign_dates", "start_at", "end_at"),
    )

    campaign_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    channel_id: Mapped[str] = mapped_column(String(32), ForeignKey("channel.channel_id"), nullable=False)
    budget_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    objective: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    channel: Mapped["Channel"] = relationship("Channel", back_populates="campaigns")
    touchpoints: Mapped[list["Touchpoint"]] = relationship("Touchpoint", back_populates="campaign")
    cost_records: Mapped[list["CostRecord"]] = relationship("CostRecord", back_populates="campaign")
    attribution_results: Mapped[list["AttributionResult"]] = relationship("AttributionResult", back_populates="campaign")


class Creative(Base):
    __tablename__ = "creative"
    __table_args__ = (
        CheckConstraint("active_to IS NULL OR active_to >= active_from", name="chk_creative_dates"),
    )

    creative_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    format: Mapped[str] = mapped_column(String(30), nullable=False)
    version: Mapped[str] = mapped_column(String(30), nullable=False)
    active_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    active_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)


class Audience(Base):
    __tablename__ = "audience"
    __table_args__ = (
        CheckConstraint("effective_to IS NULL OR effective_to >= effective_from", name="chk_audience_dates"),
    )

    audience_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    segment_type: Mapped[str] = mapped_column(String(40), nullable=False)
    criteria_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    effective_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class Contact(Base):
    __tablename__ = "contact"
    __table_args__ = (
        CheckConstraint("is_synthetic = TRUE", name="chk_contact_is_synthetic"),
        Index("idx_contact_created", "created_at"),
    )

    contact_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    region: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    customer_segment: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    consent_status: Mapped[str] = mapped_column(String(20), nullable=False)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    identity_status: Mapped[str] = mapped_column(String(20), nullable=False)

    touchpoints: Mapped[list["Touchpoint"]] = relationship("Touchpoint", back_populates="contact")
    web_sessions: Mapped[list["WebSession"]] = relationship("WebSession", back_populates="contact")
    leads: Mapped[list["Lead"]] = relationship("Lead", back_populates="contact")
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="contact")


class CampaignCreative(Base):
    __tablename__ = "campaign_creative"
    __table_args__ = (
        CheckConstraint("effective_to IS NULL OR effective_to >= effective_from", name="chk_cmp_creative_dates"),
    )

    campaign_id: Mapped[str] = mapped_column(String(32), ForeignKey("campaign.campaign_id"), primary_key=True)
    creative_id: Mapped[str] = mapped_column(String(32), ForeignKey("creative.creative_id"), primary_key=True)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    effective_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class CampaignAudience(Base):
    __tablename__ = "campaign_audience"
    __table_args__ = (
        CheckConstraint("effective_to IS NULL OR effective_to >= effective_from", name="chk_cmp_audience_dates"),
    )

    campaign_id: Mapped[str] = mapped_column(String(32), ForeignKey("campaign.campaign_id"), primary_key=True)
    audience_id: Mapped[str] = mapped_column(String(32), ForeignKey("audience.audience_id"), primary_key=True)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    effective_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class Touchpoint(Base):
    __tablename__ = "touchpoint"
    __table_args__ = (
        Index("idx_touchpoint_contact", "contact_id"),
        Index("idx_touchpoint_campaign", "campaign_id"),
        Index("idx_touchpoint_occurred", "occurred_at"),
    )

    touchpoint_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    contact_id: Mapped[Optional[str]] = mapped_column(String(32), ForeignKey("contact.contact_id"), nullable=True)
    campaign_id: Mapped[Optional[str]] = mapped_column(String(32), ForeignKey("campaign.campaign_id"), nullable=True)
    channel_id: Mapped[str] = mapped_column(String(32), ForeignKey("channel.channel_id"), nullable=False)
    creative_id: Mapped[Optional[str]] = mapped_column(String(32), ForeignKey("creative.creative_id"), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    touch_type: Mapped[str] = mapped_column(String(30), nullable=False)
    touch_mode: Mapped[str] = mapped_column(String(12), nullable=False)
    source_event_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    identity_evidence: Mapped[str] = mapped_column(String(30), nullable=False)
    issue_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    contact: Mapped[Optional["Contact"]] = relationship("Contact", back_populates="touchpoints")
    campaign: Mapped[Optional["Campaign"]] = relationship("Campaign", back_populates="touchpoints")
    channel: Mapped["Channel"] = relationship("Channel", back_populates="touchpoints")


class WebSession(Base):
    __tablename__ = "web_session"
    __table_args__ = (
        CheckConstraint("ended_at IS NULL OR ended_at >= started_at", name="chk_session_dates"),
        Index("idx_session_contact", "contact_id"),
        Index("idx_session_campaign", "campaign_id"),
        Index("idx_session_started", "started_at"),
    )

    session_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    contact_id: Mapped[Optional[str]] = mapped_column(String(32), ForeignKey("contact.contact_id"), nullable=True)
    campaign_id: Mapped[Optional[str]] = mapped_column(String(32), ForeignKey("campaign.campaign_id"), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    source_channel_id: Mapped[Optional[str]] = mapped_column(String(32), ForeignKey("channel.channel_id"), nullable=True)
    landing_path: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    identity_evidence: Mapped[str] = mapped_column(String(30), nullable=False)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    issue_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    contact: Mapped[Optional["Contact"]] = relationship("Contact", back_populates="web_sessions")


class Lead(Base):
    __tablename__ = "lead"
    __table_args__ = (
        CheckConstraint("qualification_at IS NULL OR qualification_at >= created_at", name="chk_lead_qual_dates"),
        Index("idx_lead_contact", "contact_id"),
        Index("idx_lead_session", "session_id"),
    )

    lead_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    contact_id: Mapped[str] = mapped_column(String(32), ForeignKey("contact.contact_id"), nullable=False)
    session_id: Mapped[Optional[str]] = mapped_column(String(32), ForeignKey("web_session.session_id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    qualification_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    issue_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    contact: Mapped["Contact"] = relationship("Contact", back_populates="leads")
    opportunities: Mapped[list["Opportunity"]] = relationship("Opportunity", back_populates="lead")


class Opportunity(Base):
    __tablename__ = "opportunity"
    __table_args__ = (
        CheckConstraint("expected_value >= 0", name="chk_opp_expected_value"),
        CheckConstraint("closed_at IS NULL OR closed_at >= created_at", name="chk_opp_closed_dates"),
        Index("idx_opp_lead", "lead_id"),
        Index("idx_opp_status", "status"),
    )

    opportunity_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    lead_id: Mapped[str] = mapped_column(String(32), ForeignKey("lead.lead_id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expected_value: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_closed_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    issue_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    lead: Mapped["Lead"] = relationship("Lead", back_populates="opportunities")
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="opportunity")
    events: Mapped[list["OpportunityEvent"]] = relationship("OpportunityEvent", back_populates="opportunity")


class Order(Base):
    __tablename__ = "order"
    __table_args__ = (
        CheckConstraint("gross_amount >= 0", name="chk_order_gross"),
        CheckConstraint("refund_amount >= 0 AND refund_amount <= gross_amount", name="chk_order_refund"),
        CheckConstraint("net_revenue >= 0", name="chk_order_net"),
        Index("idx_order_contact", "contact_id"),
        Index("idx_order_opportunity", "opportunity_id"),
        Index("idx_order_ordered_at", "ordered_at"),
        Index("idx_order_economic_key", "economic_transaction_key"),
    )

    order_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    opportunity_id: Mapped[Optional[str]] = mapped_column(String(32), ForeignKey("opportunity.opportunity_id"), nullable=True)
    contact_id: Mapped[str] = mapped_column(String(32), ForeignKey("contact.contact_id"), nullable=False)
    ordered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    refund_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    net_revenue: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    economic_transaction_key: Mapped[str] = mapped_column(String(80), nullable=False)
    issue_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    opportunity: Mapped[Optional["Opportunity"]] = relationship("Opportunity", back_populates="orders")
    contact: Mapped["Contact"] = relationship("Contact", back_populates="orders")
    attribution_results: Mapped[list["AttributionResult"]] = relationship("AttributionResult", back_populates="order")
    events: Mapped[list["OrderEvent"]] = relationship("OrderEvent", back_populates="order")


class CostRecord(Base):
    __tablename__ = "cost_record"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="chk_cost_amount"),
        Index("idx_cost_campaign", "campaign_id"),
        Index("idx_cost_incurred", "incurred_at"),
    )

    cost_record_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(32), ForeignKey("campaign.campaign_id"), nullable=False)
    incurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    cost_type: Mapped[str] = mapped_column(String(30), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    exchange_rate_to_reporting: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 8), nullable=True)
    reporting_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    rate_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    source_reference: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    issue_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="cost_records")


class AttributionResult(Base):
    __tablename__ = "attribution_result"
    __table_args__ = (
        CheckConstraint("credit_share >= 0 AND credit_share <= 1", name="chk_attr_credit_share"),
        CheckConstraint("attributed_revenue >= 0", name="chk_attr_revenue"),
        Index("idx_attr_order", "order_id"),
        Index("idx_attr_campaign", "campaign_id"),
        Index("idx_attr_model", "model_name", "model_version"),
    )

    attribution_result_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    order_id: Mapped[str] = mapped_column(String(32), ForeignKey("order.order_id"), nullable=False)
    campaign_id: Mapped[Optional[str]] = mapped_column(String(32), ForeignKey("campaign.campaign_id"), nullable=True)
    model_name: Mapped[str] = mapped_column(String(30), nullable=False)
    model_version: Mapped[str] = mapped_column(String(20), nullable=False)
    credit_share: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    attributed_revenue: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    decision_reason: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    run_id: Mapped[str] = mapped_column(String(40), nullable=False)
    issue_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    order: Mapped["Order"] = relationship("Order", back_populates="attribution_results")
    campaign: Mapped[Optional["Campaign"]] = relationship("Campaign", back_populates="attribution_results")
    touchpoint_links: Mapped[list["AttributionTouchpoint"]] = relationship("AttributionTouchpoint", back_populates="attribution_result")


class AttributionTouchpoint(Base):
    __tablename__ = "attribution_touchpoint"
    __table_args__ = (
        CheckConstraint("contribution_weight >= 0", name="chk_atrp_weight"),
    )

    attribution_result_id: Mapped[str] = mapped_column(String(80), ForeignKey("attribution_result.attribution_result_id"), primary_key=True)
    touchpoint_id: Mapped[str] = mapped_column(String(80), ForeignKey("touchpoint.touchpoint_id"), primary_key=True)
    contribution_weight: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)

    attribution_result: Mapped["AttributionResult"] = relationship("AttributionResult", back_populates="touchpoint_links")
    touchpoint: Mapped["Touchpoint"] = relationship("Touchpoint")


class OpportunityEvent(Base):
    __tablename__ = "opportunity_event"
    __table_args__ = (
        Index("idx_opp_event_opp", "opportunity_id"),
    )

    opportunity_event_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    opportunity_id: Mapped[str] = mapped_column(String(32), ForeignKey("opportunity.opportunity_id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    old_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    new_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    event_payload: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    run_id: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)

    opportunity: Mapped["Opportunity"] = relationship("Opportunity", back_populates="events")


class OrderEvent(Base):
    __tablename__ = "order_event"
    __table_args__ = (
        Index("idx_order_event_order", "order_id"),
    )

    order_event_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    order_id: Mapped[str] = mapped_column(String(32), ForeignKey("order.order_id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    old_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    new_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    event_payload: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    run_id: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)

    order: Mapped["Order"] = relationship("Order", back_populates="events")


class PipelineRun(Base):
    __tablename__ = "pipeline_run"

    run_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    seed: Mapped[int] = mapped_column(Integer, nullable=False)
    generator_version: Mapped[str] = mapped_column(String(20), nullable=False)
    config_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    dataset_scale: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    row_counts_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    checksums_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)


class DataIssue(Base):
    __tablename__ = "data_issue"
    __table_args__ = (
        Index("idx_issue_entity", "entity_type", "entity_id"),
    )

    issue_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    run_id: Mapped[Optional[str]] = mapped_column(String(40), ForeignKey("pipeline_run.run_id"), nullable=True)
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(80), nullable=False)
    issue_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    decision: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    resolution_status: Mapped[str] = mapped_column(String(20), default="OPEN", nullable=False)
    details_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)


class ValidationResult(Base):
    __tablename__ = "validation_result"

    validation_result_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    run_id: Mapped[Optional[str]] = mapped_column(String(40), ForeignKey("pipeline_run.run_id"), nullable=True)
    check_name: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_name: Mapped[str] = mapped_column(String(40), nullable=False)
    records_checked: Mapped[int] = mapped_column(Integer, nullable=False)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    details_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

