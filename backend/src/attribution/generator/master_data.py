"""Deterministic generation of master data: Channels, Creatives, Audiences, Campaigns, and Bridges."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import random
from typing import Any

from src.attribution.ids import DeterministicIDGenerator


# Standard Channels
CHANNEL_DEFINITIONS = [
    ("Google Search", "PAID_SEARCH"),
    ("Google Display", "DISPLAY"),
    ("LinkedIn Ads", "PAID_SOCIAL"),
    ("Meta Ads", "PAID_SOCIAL"),
    ("Email Newsletter", "EMAIL"),
    ("Organic Search", "ORGANIC"),
    ("Partner Referral", "REFERRAL"),
    ("Trade Conference", "OFFLINE"),
    ("Print & Direct Mail", "OFFLINE"),
    ("YouTube Video Ads", "DISPLAY"),
]

CREATIVE_TEMPLATES = [
    ("Enterprise Cloud Suite Banner", "BANNER", "v1.0"),
    ("ROI Calculator Interactive", "LANDING_PAGE", "v2.1"),
    ("Customer Case Study Video", "VIDEO", "v1.2"),
    ("Search Headline - Best Enterprise Tool", "TEXT", "v3.0"),
    ("Quarterly Product Demo Webinar", "LANDING_PAGE", "v1.0"),
    ("Whitepaper Download Promo", "BANNER", "v2.0"),
    ("Product Launch Video Clip", "VIDEO", "v1.0"),
    ("Industry Benchmark Report Ad", "TEXT", "v1.5"),
]

AUDIENCE_TEMPLATES = [
    ("C-Level Tech Executives", "BUSINESS"),
    ("Mid-Market Growth Companies", "BUSINESS"),
    ("High Intent Website Visitors", "HIGH_INTENT"),
    ("Inbound Webinar Attendees", "RETURNING"),
    ("General Awareness Broad Tech", "GENERAL"),
    ("Previous Demo Request Drops", "RETURNING"),
    ("Enterprise IT Procurement", "BUSINESS"),
]

CAMPAIGN_OBJECTIVES = [
    "LEAD_GENERATION",
    "BRAND_AWARENESS",
    "PRODUCT_LAUNCH",
    "CUSTOMER_ACQUISITION",
    "RETARGETING",
]

CAMPAIGN_STATUSES = ["ACTIVE", "COMPLETED", "PAUSED", "PLANNED"]


def generate_channels(id_gen: DeterministicIDGenerator, base_time: datetime) -> list[dict[str, Any]]:
    """Generate master channel records."""
    channels = []
    for name, channel_type in CHANNEL_DEFINITIONS:
        cid = id_gen.channel_id()
        channels.append({
            "channel_id": cid,
            "name": name,
            "channel_type": channel_type,
            "is_active": True,
            "created_at": base_time.isoformat(),
        })
    return channels


def generate_creatives(id_gen: DeterministicIDGenerator, base_time: datetime) -> list[dict[str, Any]]:
    """Generate master creative assets."""
    creatives = []
    for name, fmt, ver in CREATIVE_TEMPLATES:
        cid = id_gen.creative_id()
        creatives.append({
            "creative_id": cid,
            "name": name,
            "format": fmt,
            "version": ver,
            "active_from": base_time.isoformat(),
            "active_to": None,
            "metadata_json": {"asset_type": fmt.lower(), "tag": "core_2026"},
        })
    return creatives


def generate_audiences(id_gen: DeterministicIDGenerator, base_time: datetime) -> list[dict[str, Any]]:
    """Generate master audience segments."""
    audiences = []
    for name, seg_type in AUDIENCE_TEMPLATES:
        aid = id_gen.audience_id()
        audiences.append({
            "audience_id": aid,
            "name": name,
            "segment_type": seg_type,
            "criteria_json": {"industry": "Technology", "min_revenue_usd": 1000000},
            "effective_from": base_time.isoformat(),
            "effective_to": None,
        })
    return audiences


def generate_campaigns(
    count: int,
    channels: list[dict[str, Any]],
    creatives: list[dict[str, Any]],
    audiences: list[dict[str, Any]],
    id_gen: DeterministicIDGenerator,
    rng: random.Random,
    reporting_currency: str = "INR",
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Generate campaigns and their temporal bridges to creatives and audiences."""
    campaigns = []
    campaign_creatives = []
    campaign_audiences = []

    base_start = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    max_days = 270  # Campaign starts between Jan and Sep 2026

    # Currency mix
    currencies = [reporting_currency, reporting_currency, reporting_currency, "USD", "AUD"]

    for i in range(count):
        cmp_id = id_gen.campaign_id()
        channel = channels[i % len(channels)]
        
        # Duration between 30 and 180 days
        start_offset = rng.randint(0, max_days)
        duration_days = rng.randint(30, 180)
        start_at = base_start + timedelta(days=start_offset)
        end_at = start_at + timedelta(days=duration_days)

        budget = Decimal(str(rng.randint(20000, 500000)))
        status = rng.choice(CAMPAIGN_STATUSES)
        objective = rng.choice(CAMPAIGN_OBJECTIVES)
        currency = rng.choice(currencies)

        cmp_name = f"{channel['name']} - {objective.replace('_', ' ').title()} {start_at.strftime('%b %Y')} #{i+1}"

        campaigns.append({
            "campaign_id": cmp_id,
            "name": cmp_name,
            "channel_id": channel["channel_id"],
            "budget_amount": float(budget),
            "currency": currency,
            "start_at": start_at.isoformat(),
            "end_at": end_at.isoformat(),
            "status": status,
            "objective": objective,
            "created_at": base_start.isoformat(),
        })

        # Link 1-3 creatives per campaign
        num_creatives = rng.randint(1, min(3, len(creatives)))
        selected_creatives = rng.sample(creatives, num_creatives)
        for cr in selected_creatives:
            campaign_creatives.append({
                "campaign_id": cmp_id,
                "creative_id": cr["creative_id"],
                "effective_from": start_at.isoformat(),
                "effective_to": end_at.isoformat(),
            })

        # Link 1-2 audiences per campaign
        num_audiences = rng.randint(1, min(2, len(audiences)))
        selected_audiences = rng.sample(audiences, num_audiences)
        for aud in selected_audiences:
            campaign_audiences.append({
                "campaign_id": cmp_id,
                "audience_id": aud["audience_id"],
                "effective_from": start_at.isoformat(),
                "effective_to": end_at.isoformat(),
            })

    return campaigns, campaign_creatives, campaign_audiences

