# Data Dictionary

Comprehensive field-level specification for all entities in the Marketing Campaign Attribution & ROI Analysis System.

---

## 1. `channel`
- `channel_id` (VARCHAR(32), PK): Immutable unique identifier, format `CH-{counter:06d}`.
- `name` (VARCHAR(80), NOT NULL, UNIQUE): Normalized channel name.
- `channel_type` (VARCHAR(30), NOT NULL): Enum: `PAID_SEARCH`, `PAID_SOCIAL`, `EMAIL`, `ORGANIC`, `REFERRAL`, `OFFLINE`, `DISPLAY`, `OTHER`.
- `is_active` (BOOLEAN, NOT NULL): Default true.
- `created_at` (TIMESTAMPTZ, NOT NULL): Creation timestamp in UTC.

---

## 2. `campaign`
- `campaign_id` (VARCHAR(32), PK): Immutable unique identifier, format `CMP-2026-{counter:06d}`.
- `name` (VARCHAR(160), NOT NULL): Campaign descriptive title.
- `channel_id` (VARCHAR(32), FK -> channel): Primary marketing channel.
- `budget_amount` (NUMERIC(18,2), NOT NULL): Planned spend budget (>= 0).
- `currency` (CHAR(3), NOT NULL): ISO currency code (`INR`, `USD`, etc.).
- `start_at` (TIMESTAMPTZ, NOT NULL): Campaign start timestamp.
- `end_at` (TIMESTAMPTZ, NOT NULL): Campaign end timestamp (must be >= `start_at`).
- `status` (VARCHAR(20), NOT NULL): Status enum (`DRAFT`, `PLANNED`, `ACTIVE`, `PAUSED`, `COMPLETED`, `CANCELLED`).
- `objective` (VARCHAR(80), NULLABLE): Strategic goal category.
- `created_at` (TIMESTAMPTZ, NOT NULL): Metadata creation timestamp.

---

## 3. `creative`
- `creative_id` (VARCHAR(32), PK): Format `CRE-{counter:06d}`.
- `name` (VARCHAR(120), NOT NULL): Creative title.
- `format` (VARCHAR(30), NOT NULL): Enum: `TEXT`, `IMAGE`, `VIDEO`, `LANDING_PAGE`, `BANNER`, `OTHER`.
- `version` (VARCHAR(30), NOT NULL): Creative asset version string.
- `active_from` (TIMESTAMPTZ, NOT NULL): Deployment start timestamp.
- `active_to` (TIMESTAMPTZ, NULLABLE): Optional expiry timestamp.
- `metadata_json` (JSONB, NULLABLE): Synthetic non-PII attributes.

---

## 4. `audience`
- `audience_id` (VARCHAR(32), PK): Format `AUD-{counter:06d}`.
- `name` (VARCHAR(120), NOT NULL): Audience segment name.
- `segment_type` (VARCHAR(40), NOT NULL): Enum: `NEW`, `RETURNING`, `HIGH_INTENT`, `GENERAL`, `BUSINESS`, `OTHER`.
- `criteria_json` (JSONB, NULLABLE): Segment criteria definition.
- `effective_from` (TIMESTAMPTZ, NOT NULL): Start timestamp.
- `effective_to` (TIMESTAMPTZ, NULLABLE): Optional retirement timestamp.

---

## 5. `contact`
- `contact_id` (VARCHAR(32), PK): Format `CON-{counter:06d}`.
- `created_at` (TIMESTAMPTZ, NOT NULL): Synthetic contact creation time.
- `region` (VARCHAR(40), NULLABLE): Synthetic region label.
- `customer_segment` (VARCHAR(40), NULLABLE): Value tier or segment.
- `consent_status` (VARCHAR(20), NOT NULL): Enum: `UNKNOWN`, `GRANTED`, `DENIED`, `WITHDRAWN`.
- `is_synthetic` (BOOLEAN, NOT NULL): Must be TRUE.
- `identity_status` (VARCHAR(20), NOT NULL): Enum: `KNOWN`, `PARTIAL`, `UNRESOLVED`.

---

## 6. `campaign_creative` (Bridge)
- `campaign_id` (VARCHAR(32), PK, FK -> campaign)
- `creative_id` (VARCHAR(32), PK, FK -> creative)
- `effective_from` (TIMESTAMPTZ, PK): Assignment start time.
- `effective_to` (TIMESTAMPTZ, NULLABLE): Optional end time.

---

## 7. `campaign_audience` (Bridge)
- `campaign_id` (VARCHAR(32), PK, FK -> campaign)
- `audience_id` (VARCHAR(32), PK, FK -> audience)
- `effective_from` (TIMESTAMPTZ, PK): Targeting start time.
- `effective_to` (TIMESTAMPTZ, NULLABLE): Optional end time.

---

## 8. `touchpoint`
- `touchpoint_id` (VARCHAR(80), PK): Format `TOUCH-{contact_id}-{counter:06d}` or `TOUCH-ANON-{counter:06d}`.
- `contact_id` (VARCHAR(32), NULLABLE, FK -> contact): Nullable only for anonymous events.
- `campaign_id` (VARCHAR(32), NULLABLE, FK -> campaign): Nullable only for explicitly unattributed touches.
- `channel_id` (VARCHAR(32), NOT NULL, FK -> channel): Channel reference.
- `creative_id` (VARCHAR(32), NULLABLE, FK -> creative): Optional creative reference.
- `occurred_at` (TIMESTAMPTZ, NOT NULL): Interaction timestamp.
- `touch_type` (VARCHAR(30), NOT NULL): Enum: `IMPRESSION`, `CLICK`, `EMAIL_OPEN`, `EMAIL_CLICK`, `FORM_SUBMIT`, `PHONE_CALL`, `EVENT_ATTENDANCE`, `SALES_TOUCH`, `OTHER`.
- `touch_mode` (VARCHAR(12), NOT NULL): Enum: `ONLINE`, `OFFLINE`.
- `source_event_id` (VARCHAR(80), NULLABLE): External upstream identifier.
- `identity_evidence` (VARCHAR(30), NOT NULL): Enum: `AUTHENTICATED`, `CONSENTED_MATCH`, `SESSION_LINK`, `NONE`, `UNKNOWN`.
- `issue_type` (VARCHAR(50), NULLABLE): Populated for injected anomaly fixtures.
- `is_synthetic` (BOOLEAN, NOT NULL): Must be TRUE.

---

## 9. `web_session`
- `session_id` (VARCHAR(32), PK): Format `SES-2026-{counter:06d}`.
- `contact_id` (VARCHAR(32), NULLABLE, FK -> contact): Linked contact.
- `campaign_id` (VARCHAR(32), NULLABLE, FK -> campaign): Sourced campaign via verified UTM.
- `started_at` (TIMESTAMPTZ, NOT NULL): Session initiation time.
- `ended_at` (TIMESTAMPTZ, NULLABLE): Session termination time.
- `source_channel_id` (VARCHAR(32), NULLABLE, FK -> channel).
- `landing_path` (VARCHAR(200), NULLABLE): Landing URL path.
- `identity_evidence` (VARCHAR(30), NOT NULL): Evidence backing contact linkage.
- `is_anonymous` (BOOLEAN, NOT NULL): If true, `contact_id` must be null unless valid evidence exists.
- `issue_type` (VARCHAR(50), NULLABLE).

---

## 10. `lead`
- `lead_id` (VARCHAR(32), PK): Format `LEAD-2026-{counter:06d}`.
- `contact_id` (VARCHAR(32), NOT NULL, FK -> contact).
- `session_id` (VARCHAR(32), NULLABLE, FK -> web_session).
- `created_at` (TIMESTAMPTZ, NOT NULL).
- `status` (VARCHAR(20), NOT NULL): Enum: `NEW`, `QUALIFIED`, `DISQUALIFIED`, `CONVERTED`, `CLOSED`.
- `source_type` (VARCHAR(20), NOT NULL): Enum: `WEB`, `OFFLINE`, `REFERRAL`, `SALES`, `OTHER`.
- `qualification_at` (TIMESTAMPTZ, NULLABLE): >= `created_at`.
- `issue_type` (VARCHAR(50), NULLABLE).

---

## 11. `opportunity`
- `opportunity_id` (VARCHAR(32), PK): Format `OPP-2026-{counter:06d}`.
- `lead_id` (VARCHAR(32), NOT NULL, FK -> lead).
- `created_at` (TIMESTAMPTZ, NOT NULL): >= lead `created_at`.
- `expected_value` (NUMERIC(18,2), NOT NULL): Pipeline deal size (>= 0).
- `currency` (CHAR(3), NOT NULL): Currency code.
- `status` (VARCHAR(20), NOT NULL): Enum: `OPEN`, `QUALIFIED`, `PROPOSAL`, `WON`, `LOST`, `CANCELLED`.
- `closed_at` (TIMESTAMPTZ, NULLABLE): Required for `WON`/`LOST`.
- `actual_closed_value` (NUMERIC(18,2), NULLABLE): Final deal size.
- `issue_type` (VARCHAR(50), NULLABLE).

---

## 12. `order`
- `order_id` (VARCHAR(32), PK): Format `ORD-2026-{counter:06d}`.
- `opportunity_id` (VARCHAR(32), NULLABLE, FK -> opportunity).
- `contact_id` (VARCHAR(32), NOT NULL, FK -> contact).
- `ordered_at` (TIMESTAMPTZ, NOT NULL): Conversion timestamp.
- `status` (VARCHAR(20), NOT NULL): Enum: `PENDING`, `PAID`, `REFUNDED`, `PARTIALLY_REFUNDED`, `CANCELLED`.
- `gross_amount` (NUMERIC(18,2), NOT NULL): >= 0.
- `refund_amount` (NUMERIC(18,2), NOT NULL): >= 0 and <= `gross_amount`.
- `net_revenue` (NUMERIC(18,2), NOT NULL): Derived `gross_amount - refund_amount`.
- `currency` (CHAR(3), NOT NULL).
- `economic_transaction_key` (VARCHAR(80), NOT NULL): Unique transaction key across clean transactions.
- `issue_type` (VARCHAR(50), NULLABLE).

---

## 13. `cost_record`
- `cost_record_id` (VARCHAR(32), PK): Format `COST-2026-{counter:06d}`.
- `campaign_id` (VARCHAR(32), NOT NULL, FK -> campaign).
- `incurred_at` (TIMESTAMPTZ, NOT NULL).
- `cost_type` (VARCHAR(30), NOT NULL): Enum: `MEDIA`, `AGENCY`, `PRODUCTION`, `PLATFORM`, `OTHER`.
- `amount` (NUMERIC(18,2), NOT NULL): Incurred cost (>= 0).
- `currency` (CHAR(3), NOT NULL).
- `exchange_rate_to_reporting` (NUMERIC(18,8), NULLABLE): Rate applied to reach reporting currency.
- `reporting_amount` (NUMERIC(18,2), NULLABLE): Normalized cost amount.
- `rate_date` (DATE, NULLABLE): Date of exchange rate lookup.
- `source_reference` (VARCHAR(80), NULLABLE).
- `issue_type` (VARCHAR(50), NULLABLE).

---

## 14. `attribution_result`
- `attribution_result_id` (VARCHAR(80), PK): Deterministic key `ATTR-{order_id}-{model}-{campaign_id}`.
- `order_id` (VARCHAR(32), NOT NULL, FK -> order).
- `campaign_id` (VARCHAR(32), NULLABLE, FK -> campaign): Null for unattributed bucket.
- `model_name` (VARCHAR(30), NOT NULL): Enum: `FIRST_TOUCH`, `LAST_TOUCH`, `LINEAR`.
- `model_version` (VARCHAR(20), NOT NULL): Rule version string.
- `credit_share` (NUMERIC(9,6), NOT NULL): Share in [0.0, 1.0].
- `attributed_revenue` (NUMERIC(18,2), NOT NULL): Revenue allocated to the cent.
- `calculated_at` (TIMESTAMPTZ, NOT NULL).
- `decision_reason` (VARCHAR(200), NULLABLE).
- `run_id` (VARCHAR(40), NOT NULL).
- `issue_type` (VARCHAR(50), NULLABLE).

---

## 15. `attribution_touchpoint`
- `attribution_result_id` (VARCHAR(80), PK, FK -> attribution_result).
- `touchpoint_id` (VARCHAR(80), PK, FK -> touchpoint).
- `contribution_weight` (NUMERIC(9,6), NOT NULL): Touchpoint weighting within campaign credit.

---

## 16. `opportunity_event` & `order_event`
- Append-only event logs with `event_type`, `old_status`, `new_status`, `occurred_at`, `event_payload` (JSONB), and `run_id`.

