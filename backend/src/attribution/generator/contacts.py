"""Deterministic generation of synthetic Contacts."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import random
from typing import Any

from src.attribution.ids import DeterministicIDGenerator


REGIONS = ["APAC", "EMEA", "NAM", "LATAM"]
SEGMENTS = ["SMB", "MID_MARKET", "ENTERPRISE", "STARTUP"]
CONSENT_CHOICES = ["GRANTED", "GRANTED", "GRANTED", "UNKNOWN", "DENIED", "WITHDRAWN"]
IDENTITY_STATUSES = ["KNOWN", "KNOWN", "KNOWN", "PARTIAL", "UNRESOLVED"]


def generate_contacts(
    count: int,
    id_gen: DeterministicIDGenerator,
    rng: random.Random,
    start_date: datetime | None = None,
    time_span_days: int = 270,
) -> list[dict[str, Any]]:
    """Generate deterministic synthetic contact records."""
    if start_date is None:
        start_date = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    contacts = []
    for _ in range(count):
        cid = id_gen.contact_id()
        offset_seconds = rng.randint(0, time_span_days * 86400)
        created_at = start_date + timedelta(seconds=offset_seconds)
        
        region = rng.choice(REGIONS)
        segment = rng.choice(SEGMENTS)
        consent = rng.choice(CONSENT_CHOICES)
        identity = rng.choice(IDENTITY_STATUSES)

        contacts.append({
            "contact_id": cid,
            "created_at": created_at.isoformat(),
            "region": region,
            "customer_segment": segment,
            "consent_status": consent,
            "is_synthetic": True,
            "identity_status": identity,
        })

    # Sort deterministically by contact_id
    contacts.sort(key=lambda x: x["contact_id"])
    return contacts

