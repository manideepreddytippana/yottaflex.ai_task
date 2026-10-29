"""Modular business logic and data access services for the Attribution system."""

from __future__ import annotations

from src.attribution.services.base import BaseService, PROJECT_ROOT
from src.attribution.services.health import HealthService
from src.attribution.services.runs import RunService
from src.attribution.services.campaigns import CampaignService
from src.attribution.services.attribution import AttributionService
from src.attribution.services.contacts import ContactService
from src.attribution.services.issues import IssueService
from src.attribution.services.metrics import MetricsService
from src.attribution.services.exports import ExportService


class UnifiedAttributionService(
    HealthService,
    RunService,
    CampaignService,
    AttributionService,
    ContactService,
    IssueService,
    MetricsService,
    ExportService,
):
    """Unified composite service combining all domain services for convenient access."""
    pass


__all__ = [
    "BaseService",
    "PROJECT_ROOT",
    "HealthService",
    "RunService",
    "CampaignService",
    "AttributionService",
    "ContactService",
    "IssueService",
    "MetricsService",
    "ExportService",
    "UnifiedAttributionService",
]

