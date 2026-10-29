"""Configuration schema, validation, and loader for the Marketing Attribution System."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal
import yaml
from pydantic import BaseModel, Field, field_validator


class CountsConfig(BaseModel):
    """Target counts for data generation."""
    campaigns: int = Field(gt=0, description="Number of campaigns to generate")
    contacts: int = Field(gt=0, description="Number of contacts to generate")
    touchpoints: int = Field(gt=0, description="Target number of touchpoints")
    opportunities: int = Field(gt=0, description="Target number of opportunities")


class AnomalyRatesConfig(BaseModel):
    """Injected anomaly rates per opportunity/order/cost/touchpoint."""
    duplicate_revenue: float = Field(default=0.002, ge=0.0, le=1.0)
    post_conversion_touch: float = Field(default=0.002, ge=0.0, le=1.0)
    currency_mismatch: float = Field(default=0.002, ge=0.0, le=1.0)
    missing_campaign_cost: float = Field(default=0.002, ge=0.0, le=1.0)
    unsupported_identity_link: float = Field(default=0.002, ge=0.0, le=1.0)


class SystemConfig(BaseModel):
    """Master configuration for synthetic generation and pipeline runs."""
    seed: int = Field(default=20261022, description="Fixed PRNG seed for deterministic runs")
    dataset_scale: Literal["starter", "full", "custom"] = Field(default="starter")
    reporting_currency: str = Field(default="INR", min_length=3, max_length=3)
    counts: CountsConfig
    conversion_window_days: int = Field(default=180, gt=0)
    anomaly_injection_enabled: bool = Field(default=True)
    anomaly_rates: AnomalyRatesConfig = Field(default_factory=AnomalyRatesConfig)

    @field_validator("reporting_currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        return v.upper()

    def get_config_hash(self) -> str:
        """Compute deterministic SHA-256 hash of the normalized configuration."""
        dumped = json.dumps(self.model_dump(), sort_keys=True)
        return hashlib.sha256(dumped.encode("utf-8")).hexdigest()


def load_config(path: str | Path) -> SystemConfig:
    """Load and validate configuration from a YAML file."""
    config_path = Path(path)
    if not config_path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Invalid YAML configuration format in {config_path}")

    return SystemConfig.model_validate(data)

