"""Unit tests for configuration loading and validation."""

import pytest
from pathlib import Path
from pydantic import ValidationError
from src.attribution.config import (
    AnomalyRatesConfig,
    CountsConfig,
    SystemConfig,
    load_config,
)


def test_load_starter_config():
    config = load_config("config/starter.yaml")
    assert config.seed == 20261022
    assert config.dataset_scale == "starter"
    assert config.reporting_currency == "INR"
    assert config.counts.campaigns == 25
    assert config.counts.contacts == 1000
    assert config.counts.touchpoints == 4000
    assert config.counts.opportunities == 200
    assert config.conversion_window_days == 180
    assert config.anomaly_injection_enabled is True
    assert config.anomaly_rates.duplicate_revenue > 0


def test_load_full_config():
    config = load_config("config/full.yaml")
    assert config.seed == 20261022
    assert config.dataset_scale == "full"
    assert config.reporting_currency == "INR"
    assert config.counts.campaigns == 500
    assert config.counts.contacts == 50000
    assert config.counts.touchpoints == 200000
    assert config.counts.opportunities == 10000


def test_config_hash_determinism():
    c1 = load_config("config/starter.yaml")
    c2 = load_config("config/starter.yaml")
    assert c1.get_config_hash() == c2.get_config_hash()
    assert len(c1.get_config_hash()) == 64


def test_invalid_config_validation():
    # Negative count
    with pytest.raises(ValidationError):
        CountsConfig(campaigns=-5, contacts=100, touchpoints=100, opportunities=50)

    # Invalid anomaly rate > 1.0
    with pytest.raises(ValidationError):
        AnomalyRatesConfig(duplicate_revenue=1.5)

    # Invalid currency length
    with pytest.raises(ValidationError):
        SystemConfig(
            seed=123,
            reporting_currency="USDD",
            counts=CountsConfig(campaigns=10, contacts=10, touchpoints=10, opportunities=10),
        )

