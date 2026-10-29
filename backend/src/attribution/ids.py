"""Central deterministic ID generation and validation module.

Strictly follows Section 6 of the implementation plan:
- Campaign:    CMP-2026-{counter:06d}
- Contact:     CON-{counter:06d}
- Touchpoint:  TOUCH-{contact_id}-{counter:06d} (or TOUCH-ANON-{counter:06d})
- Session:     SES-2026-{counter:06d}
- Lead:        LEAD-2026-{counter:06d}
- Opportunity: OPP-2026-{counter:06d}
- Order:       ORD-2026-{counter:06d}
- Cost:        COST-2026-{counter:06d}
- Channel:     CH-{counter:06d}
- Creative:    CRE-{counter:06d}
- Audience:    AUD-{counter:06d}
"""

from __future__ import annotations

import re
from typing import Optional


# Regular expressions for validation
CAMPAIGN_ID_REGEX = re.compile(r"^CMP-2026-\d{6}$")
CONTACT_ID_REGEX = re.compile(r"^CON-\d{6}$")
TOUCHPOINT_KNOWN_REGEX = re.compile(r"^TOUCH-CON-\d{6}-\d{6}$")
TOUCHPOINT_ANON_REGEX = re.compile(r"^TOUCH-ANON-\d{6}$")
SESSION_ID_REGEX = re.compile(r"^SES-2026-\d{6}$")
LEAD_ID_REGEX = re.compile(r"^LEAD-2026-\d{6}$")
OPPORTUNITY_ID_REGEX = re.compile(r"^OPP-2026-\d{6}$")
ORDER_ID_REGEX = re.compile(r"^ORD-2026-\d{6}$")
COST_ID_REGEX = re.compile(r"^COST-2026-\d{6}$")
CHANNEL_ID_REGEX = re.compile(r"^CH-\d{6}$")
CREATIVE_ID_REGEX = re.compile(r"^CRE-\d{6}$")
AUDIENCE_ID_REGEX = re.compile(r"^AUD-\d{6}$")
OPP_EVENT_ID_REGEX = re.compile(r"^OPPEVT-\d{6}$")
ORDER_EVENT_ID_REGEX = re.compile(r"^ORDEVT-\d{6}$")
ISSUE_ID_REGEX = re.compile(r"^ISSUE-\d{6}$")
VALIDATION_RESULT_ID_REGEX = re.compile(r"^VAL-\d{6}$")
GROUND_TRUTH_ID_REGEX = re.compile(r"^GT-\d{6}$")


class DeterministicIDGenerator:
    """Stateful, reproducible counter-based ID generator."""

    def __init__(self, year: int = 2026) -> None:
        self.year = year
        self.counters: dict[str, int] = {}
        # Scoped counter for touchpoints per contact
        self.contact_touchpoint_counters: dict[str, int] = {}

    def reset(self) -> None:
        """Reset all counters to initial state."""
        self.counters.clear()
        self.contact_touchpoint_counters.clear()

    def _next_val(self, key: str) -> int:
        current = self.counters.get(key, 0) + 1
        self.counters[key] = current
        return current

    def campaign_id(self) -> str:
        idx = self._next_val("campaign")
        return f"CMP-{self.year}-{idx:06d}"

    def contact_id(self) -> str:
        idx = self._next_val("contact")
        return f"CON-{idx:06d}"

    def touchpoint_id(self, contact_id: Optional[str] = None) -> str:
        if contact_id:
            curr = self.contact_touchpoint_counters.get(contact_id, 0) + 1
            self.contact_touchpoint_counters[contact_id] = curr
            return f"TOUCH-{contact_id}-{curr:06d}"
        idx = self._next_val("touchpoint_anon")
        return f"TOUCH-ANON-{idx:06d}"

    def session_id(self) -> str:
        idx = self._next_val("session")
        return f"SES-{self.year}-{idx:06d}"

    def lead_id(self) -> str:
        idx = self._next_val("lead")
        return f"LEAD-{self.year}-{idx:06d}"

    def opportunity_id(self) -> str:
        idx = self._next_val("opportunity")
        return f"OPP-{self.year}-{idx:06d}"

    def order_id(self) -> str:
        idx = self._next_val("order")
        return f"ORD-{self.year}-{idx:06d}"

    def cost_id(self) -> str:
        idx = self._next_val("cost")
        return f"COST-{self.year}-{idx:06d}"

    def channel_id(self) -> str:
        idx = self._next_val("channel")
        return f"CH-{idx:06d}"

    def creative_id(self) -> str:
        idx = self._next_val("creative")
        return f"CRE-{idx:06d}"

    def audience_id(self) -> str:
        idx = self._next_val("audience")
        return f"AUD-{idx:06d}"

    def opportunity_event_id(self) -> str:
        idx = self._next_val("opportunity_event")
        return f"OPPEVT-{idx:06d}"

    def order_event_id(self) -> str:
        idx = self._next_val("order_event")
        return f"ORDEVT-{idx:06d}"

    def attribution_result_id(self, order_id: str, model_name: str, campaign_id: Optional[str] = None) -> str:
        cid = campaign_id if campaign_id else "UNATTR"
        return f"ATTR-{order_id}-{model_name}-{cid}"

    def issue_id(self) -> str:
        idx = self._next_val("issue")
        return f"ISSUE-{idx:06d}"

    def validation_result_id(self) -> str:
        idx = self._next_val("validation_result")
        return f"VAL-{idx:06d}"

    def ground_truth_id(self) -> str:
        idx = self._next_val("ground_truth")
        return f"GT-{idx:06d}"


# ID Validator functions
def is_valid_campaign_id(cid: str) -> bool:
    return bool(CAMPAIGN_ID_REGEX.match(cid))

def is_valid_contact_id(cid: str) -> bool:
    return bool(CONTACT_ID_REGEX.match(cid))

def is_valid_touchpoint_id(tid: str) -> bool:
    return bool(TOUCHPOINT_KNOWN_REGEX.match(tid) or TOUCHPOINT_ANON_REGEX.match(tid))

def is_valid_session_id(sid: str) -> bool:
    return bool(SESSION_ID_REGEX.match(sid))

def is_valid_lead_id(lid: str) -> bool:
    return bool(LEAD_ID_REGEX.match(lid))

def is_valid_opportunity_id(oid: str) -> bool:
    return bool(OPPORTUNITY_ID_REGEX.match(oid))

def is_valid_order_id(oid: str) -> bool:
    return bool(ORDER_ID_REGEX.match(oid))

def is_valid_cost_id(cid: str) -> bool:
    return bool(COST_ID_REGEX.match(cid))

def is_valid_channel_id(cid: str) -> bool:
    return bool(CHANNEL_ID_REGEX.match(cid))

def is_valid_creative_id(cid: str) -> bool:
    return bool(CREATIVE_ID_REGEX.match(cid))

def is_valid_audience_id(aid: str) -> bool:
    return bool(AUDIENCE_ID_REGEX.match(aid))

