"""Deterministic generation of marketing touchpoints with realistic skewed journeys."""

from __future__ import annotations

from datetime import datetime, timedelta
import random
from typing import Any

from src.attribution.ids import DeterministicIDGenerator


ONLINE_TOUCH_TYPES = [
    ("IMPRESSION", "ONLINE"),
    ("CLICK", "ONLINE"),
    ("EMAIL_OPEN", "ONLINE"),
    ("EMAIL_CLICK", "ONLINE"),
    ("FORM_SUBMIT", "ONLINE"),
]

OFFLINE_TOUCH_TYPES = [
    ("PHONE_CALL", "OFFLINE"),
    ("EVENT_ATTENDANCE", "OFFLINE"),
    ("SALES_TOUCH", "OFFLINE"),
]

IDENTITY_EVIDENCES = ["AUTHENTICATED", "CONSENTED_MATCH", "SESSION_LINK"]


def generate_touchpoints(
    target_count: int,
    contacts: list[dict[str, Any]],
    campaigns: list[dict[str, Any]],
    campaign_creatives: list[dict[str, Any]],
    id_gen: DeterministicIDGenerator,
    rng: random.Random,
) -> list[dict[str, Any]]:
    """Generate touchpoints with realistic multi-campaign customer journeys."""
    touchpoints: list[dict[str, Any]] = []

    # Map campaign to creatives
    cmp_to_creatives: dict[str, list[str]] = {}
    for bridge in campaign_creatives:
        cmp_to_creatives.setdefault(bridge["campaign_id"], []).append(bridge["creative_id"])

    # Anonymous touchpoints share (around 5%)
    anon_target = int(target_count * 0.05)
    contact_target = target_count - anon_target

    # Determine touch distribution across contacts (skewed)
    num_contacts = len(contacts)
    weights: list[int] = []
    for i in range(num_contacts):
        # Pareto-like distribution
        tier = rng.random()
        if tier < 0.65:
            weights.append(rng.randint(1, 3))
        elif tier < 0.90:
            weights.append(rng.randint(4, 7))
        else:
            weights.append(rng.randint(8, 18))

    total_weight = sum(weights)
    if total_weight == 0:
        total_weight = 1

    # Generate touchpoints for known contacts
    allocated = 0
    for i, contact in enumerate(contacts):
        contact_id = contact["contact_id"]
        con_created = datetime.fromisoformat(contact["created_at"])
        num_touches = max(1, int((weights[i] / total_weight) * contact_target))

        # Select 1 to 3 campaigns this contact interacts with
        num_cmps = rng.randint(1, min(3, len(campaigns)))
        chosen_campaigns = rng.sample(campaigns, num_cmps)

        current_time = con_created
        for _ in range(num_touches):
            cmp = rng.choice(chosen_campaigns)
            cmp_start = datetime.fromisoformat(cmp["start_at"])
            cmp_end = datetime.fromisoformat(cmp["end_at"])

            # Touch occurred_at between contact creation and campaign end (within initial journey window)
            earliest = max(con_created, cmp_start)
            latest = max(earliest, min(con_created + timedelta(days=20), cmp_end))
            delta_seconds = max(1, int((latest - earliest).total_seconds()))
            touch_time = earliest + timedelta(seconds=rng.randint(0, delta_seconds))

            # Decide online vs offline
            if rng.random() < 0.85:
                touch_type, touch_mode = rng.choice(ONLINE_TOUCH_TYPES)
            else:
                touch_type, touch_mode = rng.choice(OFFLINE_TOUCH_TYPES)

            # Available creative
            creatives = cmp_to_creatives.get(cmp["campaign_id"], [])
            cr_id = rng.choice(creatives) if creatives else None

            tid = id_gen.touchpoint_id(contact_id=contact_id)
            evidence = rng.choice(IDENTITY_EVIDENCES)

            touchpoints.append({
                "touchpoint_id": tid,
                "contact_id": contact_id,
                "campaign_id": cmp["campaign_id"],
                "channel_id": cmp["channel_id"],
                "creative_id": cr_id,
                "occurred_at": touch_time.isoformat(),
                "touch_type": touch_type,
                "touch_mode": touch_mode,
                "source_event_id": f"EVT-{tid}",
                "identity_evidence": evidence,
                "issue_type": None,
                "is_synthetic": True,
            })
            allocated += 1
            if allocated >= contact_target:
                break
        if allocated >= contact_target:
            break

    # Generate anonymous touchpoints
    while len(touchpoints) < target_count:
        cmp = rng.choice(campaigns)
        cmp_start = datetime.fromisoformat(cmp["start_at"])
        cmp_end = datetime.fromisoformat(cmp["end_at"])
        delta_seconds = max(1, int((cmp_end - cmp_start).total_seconds()))
        touch_time = cmp_start + timedelta(seconds=rng.randint(0, delta_seconds))

        touch_type, touch_mode = rng.choice(ONLINE_TOUCH_TYPES)
        creatives = cmp_to_creatives.get(cmp["campaign_id"], [])
        cr_id = rng.choice(creatives) if creatives else None

        tid = id_gen.touchpoint_id(contact_id=None)

        touchpoints.append({
            "touchpoint_id": tid,
            "contact_id": None,
            "campaign_id": cmp["campaign_id"],
            "channel_id": cmp["channel_id"],
            "creative_id": cr_id,
            "occurred_at": touch_time.isoformat(),
            "touch_type": touch_type,
            "touch_mode": touch_mode,
            "source_event_id": f"EVT-{tid}",
            "identity_evidence": "NONE",
            "issue_type": None,
            "is_synthetic": True,
        })

    # Sort touchpoints chronologically and tie-break on touchpoint_id
    touchpoints.sort(key=lambda t: (t["occurred_at"], t["touchpoint_id"]))
    return touchpoints

