"""Deterministic generation of Leads."""

from __future__ import annotations

from datetime import datetime, timedelta
import random
from typing import Any

from src.attribution.ids import DeterministicIDGenerator


LEAD_STATUSES = ["NEW", "QUALIFIED", "DISQUALIFIED", "CONVERTED", "CLOSED"]
LEAD_SOURCES = ["WEB", "OFFLINE", "REFERRAL", "SALES", "OTHER"]


def generate_leads(
    target_lead_count: int,
    contacts: list[dict[str, Any]],
    web_sessions: list[dict[str, Any]],
    touchpoints: list[dict[str, Any]],
    id_gen: DeterministicIDGenerator,
    rng: random.Random,
) -> list[dict[str, Any]]:
    """Generate marketing leads linked to contacts and optional web sessions."""
    leads: list[dict[str, Any]] = []

    # Map contacts to their sessions and touches
    contact_sessions: dict[str, list[dict[str, Any]]] = {}
    for sess in web_sessions:
        if sess["contact_id"]:
            contact_sessions.setdefault(sess["contact_id"], []).append(sess)

    contact_touches: dict[str, list[dict[str, Any]]] = {}
    for touch in touchpoints:
        if touch["contact_id"]:
            contact_touches.setdefault(touch["contact_id"], []).append(touch)

    # Filter contacts with interactions
    active_contacts = [c for c in contacts if c["contact_id"] in contact_touches or c["contact_id"] in contact_sessions]
    if not active_contacts:
        active_contacts = contacts

    for i in range(target_lead_count):
        lid = id_gen.lead_id()
        contact = active_contacts[i % len(active_contacts)]
        cid = contact["contact_id"]
        con_created = datetime.fromisoformat(contact["created_at"])

        # Check if contact has interactions
        touches = contact_touches.get(cid, [])
        max_touch_time = max((datetime.fromisoformat(t["occurred_at"]) for t in touches), default=con_created)

        # Check if contact has a web session
        sessions = contact_sessions.get(cid, [])
        session = rng.choice(sessions) if sessions and rng.random() < 0.75 else None

        if session:
            sess_start = datetime.fromisoformat(session["started_at"])
            lead_created = max(sess_start, max_touch_time) + timedelta(minutes=rng.randint(5, 60))
            source_type = "WEB"
            session_id = session["session_id"]
        else:
            session_id = None
            lead_created = max_touch_time + timedelta(hours=rng.randint(1, 48))
            source_type = "OFFLINE" if touches and touches[0]["touch_mode"] == "OFFLINE" else "REFERRAL"

        # Lead status
        status = rng.choice(LEAD_STATUSES)
        qual_at = None
        if status in ("QUALIFIED", "CONVERTED", "CLOSED"):
            qual_at = (lead_created + timedelta(days=rng.randint(1, 14))).isoformat()

        leads.append({
            "lead_id": lid,
            "contact_id": cid,
            "session_id": session_id,
            "created_at": lead_created.isoformat(),
            "status": status,
            "source_type": source_type,
            "qualification_at": qual_at,
            "issue_type": None,
        })

    leads.sort(key=lambda l: (l["created_at"], l["lead_id"]))
    return leads

