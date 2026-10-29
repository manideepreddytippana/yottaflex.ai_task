"""Master orchestrator for deterministic synthetic data generation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import random
from typing import Any

from src.attribution.config import SystemConfig
from src.attribution.ids import DeterministicIDGenerator
from src.attribution.generator.contacts import generate_contacts
from src.attribution.generator.costs import generate_cost_records
from src.attribution.generator.leads import generate_leads
from src.attribution.generator.master_data import (
    generate_audiences,
    generate_campaigns,
    generate_channels,
    generate_creatives,
)
from src.attribution.generator.opportunities import generate_opportunities
from src.attribution.generator.orders import generate_orders
from src.attribution.generator.touchpoints import generate_touchpoints
from src.attribution.generator.web_sessions import generate_web_sessions


@dataclass
class GeneratedDataset:
    """In-memory representation of all generated entity tables."""
    channels: list[dict[str, Any]]
    creatives: list[dict[str, Any]]
    audiences: list[dict[str, Any]]
    campaigns: list[dict[str, Any]]
    campaign_creatives: list[dict[str, Any]]
    campaign_audiences: list[dict[str, Any]]
    contacts: list[dict[str, Any]]
    touchpoints: list[dict[str, Any]]
    web_sessions: list[dict[str, Any]]
    leads: list[dict[str, Any]]
    opportunities: list[dict[str, Any]]
    opportunity_events: list[dict[str, Any]]
    orders: list[dict[str, Any]]
    order_events: list[dict[str, Any]]
    cost_records: list[dict[str, Any]]

    def get_row_counts(self) -> dict[str, int]:
        """Return dictionary of row counts per entity."""
        return {
            "channel": len(self.channels),
            "creative": len(self.creatives),
            "audience": len(self.audiences),
            "campaign": len(self.campaigns),
            "campaign_creative": len(self.campaign_creatives),
            "campaign_audience": len(self.campaign_audiences),
            "contact": len(self.contacts),
            "touchpoint": len(self.touchpoints),
            "web_session": len(self.web_sessions),
            "lead": len(self.leads),
            "opportunity": len(self.opportunities),
            "opportunity_event": len(self.opportunity_events),
            "order": len(self.orders),
            "order_event": len(self.order_events),
            "cost_record": len(self.cost_records),
        }


def generate_dataset(config: SystemConfig) -> GeneratedDataset:
    """Generate complete synthetic dataset strictly adhering to seed and configuration."""
    # Initialize deterministic PRNG and ID generator
    rng = random.Random(config.seed)
    id_gen = DeterministicIDGenerator(year=2026)
    base_time = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    # 1. Master entities
    channels = generate_channels(id_gen, base_time)
    creatives = generate_creatives(id_gen, base_time)
    audiences = generate_audiences(id_gen, base_time)
    campaigns, campaign_creatives, campaign_audiences = generate_campaigns(
        count=config.counts.campaigns,
        channels=channels,
        creatives=creatives,
        audiences=audiences,
        id_gen=id_gen,
        rng=rng,
        reporting_currency=config.reporting_currency,
    )

    # 2. Contacts
    contacts = generate_contacts(
        count=config.counts.contacts,
        id_gen=id_gen,
        rng=rng,
        start_date=base_time,
    )

    # 3. Touchpoints & Web Sessions
    touchpoints = generate_touchpoints(
        target_count=config.counts.touchpoints,
        contacts=contacts,
        campaigns=campaigns,
        campaign_creatives=campaign_creatives,
        id_gen=id_gen,
        rng=rng,
    )

    web_sessions = generate_web_sessions(
        touchpoints=touchpoints,
        id_gen=id_gen,
        rng=rng,
    )

    # 4. Leads (1.5x opportunities to ensure a realistic funnel conversion funnel)
    lead_target = max(int(config.counts.opportunities * 1.5), len(contacts) // 2)
    leads = generate_leads(
        target_lead_count=lead_target,
        contacts=contacts,
        web_sessions=web_sessions,
        touchpoints=touchpoints,
        id_gen=id_gen,
        rng=rng,
    )

    # 5. Opportunities & Opportunity Events
    opportunities, opp_events = generate_opportunities(
        target_count=config.counts.opportunities,
        leads=leads,
        id_gen=id_gen,
        rng=rng,
        reporting_currency=config.reporting_currency,
    )

    # 6. Orders & Order Events
    orders, ord_events = generate_orders(
        opportunities=opportunities,
        leads=leads,
        id_gen=id_gen,
        rng=rng,
        reporting_currency=config.reporting_currency,
    )

    # 7. Campaign Costs
    cost_records = generate_cost_records(
        campaigns=campaigns,
        id_gen=id_gen,
        rng=rng,
        reporting_currency=config.reporting_currency,
    )

    return GeneratedDataset(
        channels=channels,
        creatives=creatives,
        audiences=audiences,
        campaigns=campaigns,
        campaign_creatives=campaign_creatives,
        campaign_audiences=campaign_audiences,
        contacts=contacts,
        touchpoints=touchpoints,
        web_sessions=web_sessions,
        leads=leads,
        opportunities=opportunities,
        opportunity_events=opp_events,
        orders=orders,
        order_events=ord_events,
        cost_records=cost_records,
    )

