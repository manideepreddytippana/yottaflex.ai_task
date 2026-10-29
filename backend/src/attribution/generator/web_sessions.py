"""Deterministic generation of web sessions."""

from __future__ import annotations

from datetime import datetime, timedelta
import random
from typing import Any

from src.attribution.ids import DeterministicIDGenerator


LANDING_PATHS = [
    "/",
    "/pricing",
    "/product-demo",
    "/enterprise-cloud",
    "/solutions/fintech",
    "/case-studies/acme-corp",
    "/resources/whitepaper-roi",
    "/contact-sales",
]


def generate_web_sessions(
    touchpoints: list[dict[str, Any]],
    id_gen: DeterministicIDGenerator,
    rng: random.Random,
) -> list[dict[str, Any]]:
    """Generate web sessions derived from and accompanying online touchpoints."""
    sessions = []
    
    # Filter for online touchpoints that naturally spawn web sessions
    session_eligible_touches = [
        t for t in touchpoints if t["touch_mode"] == "ONLINE" and t["touch_type"] in ("CLICK", "FORM_SUBMIT", "IMPRESSION")
    ]

    for touch in session_eligible_touches:
        # High probability of session creation from click/form submit, moderate from impression
        prob = 0.95 if touch["touch_type"] in ("CLICK", "FORM_SUBMIT") else 0.30
        if rng.random() > prob:
            continue

        sid = id_gen.session_id()
        started_at = datetime.fromisoformat(touch["occurred_at"])
        duration_minutes = rng.randint(2, 45)
        ended_at = started_at + timedelta(minutes=duration_minutes)

        contact_id = touch["contact_id"]
        is_anon = contact_id is None
        evidence = touch["identity_evidence"] if not is_anon else "NONE"

        sessions.append({
            "session_id": sid,
            "contact_id": contact_id,
            "campaign_id": touch["campaign_id"],
            "started_at": started_at.isoformat(),
            "ended_at": ended_at.isoformat(),
            "source_channel_id": touch["channel_id"],
            "landing_path": rng.choice(LANDING_PATHS),
            "identity_evidence": evidence,
            "is_anonymous": is_anon,
            "issue_type": None,
        })

    sessions.sort(key=lambda s: (s["started_at"], s["session_id"]))
    return sessions

