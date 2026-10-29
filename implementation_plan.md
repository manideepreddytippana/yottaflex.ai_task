# Marketing Campaign Attribution & ROI Analysis System

## Detailed Implementation Plan

**Document type:** Engineering implementation plan\
**Version:** 1.0\
**Status:** Proposed\
**Fixed synthetic-data seed:** `20261022`\
**Primary objective:** Build a reproducible end-to-end pipeline that
joins campaign interactions, web activity, leads, opportunities, orders
and costs; compares attribution models; calculates campaign ROI; exposes
exceptions; and demonstrates data integrity and reproducibility.

------------------------------------------------------------------------

## 1. Executive Summary

Build a data-engineering and analytics application that generates
realistic synthetic marketing data, stores it in a relational database,
reconstructs customer journeys, applies documented attribution rules,
calculates campaign-level performance and ROI, detects known
data-quality anomalies, and exports auditable results.

The solution must do more than display charts. It must provide: - A
deterministic, parameterized synthetic-data generator. - A documented
relational schema with primary keys, foreign keys, bridge tables and
lifecycle-event history. - A validated pipeline joining campaigns,
touchpoints, web sessions, leads, opportunities, orders and costs. -
First-touch, last-touch and linear multi-touch attribution. - Financial
reconciliation and currency handling. - Detection of five required
anomaly categories. - A separate ground-truth dataset for evaluating
exception detection. - CSV, JSON and SQL seed exports. - A data
dictionary, source manifest, validation report and README. - A
repeatability test that runs the same configuration twice and compares
counts and checksums. - An optional web dashboard for exploring results.

## 2. Scope

### 2.1 In scope

1.  Generate master data: Campaign, Channel, Creative, Audience and
    Contact.
2.  Generate dependent events and transactions with valid references.
3.  Generate at least 500 campaigns, 50,000 contacts, 200,000
    touchpoints and 10,000 opportunities in full mode.
4.  Generate realistic variation: multiple campaigns per journey,
    offline touches, anonymous sessions, missing identifiers, long
    conversion windows and varied lifecycle states.
5.  Reconstruct journeys from marketing interaction to
    conversion/revenue.
6.  Calculate first-touch, last-touch and linear multi-touch
    attribution.
7.  Calculate actual spend, attributed revenue, ROI and reconciliation
    metrics.
8.  Detect and report the five specified anomalies.
9.  Preserve state changes as immutable events or history records.
10. Produce ground-truth labels separately from model/detection inputs.
11. Validate referential integrity, dates, enums, lifecycle transitions,
    duplicates and arithmetic.
12. Export data and documentation, and demonstrate reproducibility.
13. Provide APIs and a dashboard if a user-facing application is
    required.

### 2.2 Out of scope for the first version

-   Predictive machine learning or causal-incrementality estimation.
-   Live integrations with ad platforms, CRM systems, analytics
    platforms or payment providers.
-   Real customer data or confidential business data.
-   Automated remediation that silently deletes or rewrites source
    records.
-   Complex probabilistic identity resolution.
-   Production multi-tenant permissions, unless separately required.

### 2.3 Primary actors

  -----------------------------------------------------------------------
  Actor                   Main needs              First-version
                                                  capabilities
  ----------------------- ----------------------- -----------------------
  Customer/prospect       Journey interactions    Synthetic touchpoints
  (represented            are represented         and sessions
  synthetically)          accurately              

  Marketing operations    Understand campaign     Campaign and cost
                          spend and performance   reports

  Sales operations        Trace leads,            Lead-to-revenue journey
                          opportunities and       view
                          orders                  

  Support agent           Investigate data or     Exception detail and
                          attribution issues      source-record trace

  Analyst                 Compare attribution     Attribution comparison,
                          methods and evaluate    exports and metrics
                          data quality            

  System administrator    Generate data, run      Run configuration,
                          validations and inspect status and
                          run history             reproducibility report
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 3. Recommended Architecture

### 3.1 Technology choices

  -----------------------------------------------------------------------
  Layer                   Recommended technology  Reason
  ----------------------- ----------------------- -----------------------
  Generator               Python 3.11+ or a       Deterministic
                          supported stable Python generation and tabular
                          version, NumPy, Pandas  exports

  Database                PostgreSQL              Relational integrity,
                                                  joins, transactions and
                                                  reporting

  Backend API             FastAPI + Pydantic      Typed API contracts and
                                                  validation

  Data access             SQLAlchemy              Database persistence
                                                  and queries

  Frontend                React + TypeScript +    Interactive analytics
                          Vite                    UI

  Charts                  Recharts                Attribution and ROI
                                                  comparisons

  Testing                 pytest                  Unit, integration and
                                                  acceptance tests

  Data validation         Explicit Python/SQL     Reusable quality rules
                          checks; optionally      
                          Pandera                 

  Hashing                 Python `hashlib`        Repeatability
                          SHA-256                 verification

  Export                  CSV, JSON and SQL seed  Required portable
                          scripts                 deliverables

  Configuration           `.env` for secrets;     Reproducible
                          versioned config file   environments
                          for non-secret          
                          parameters              
  -----------------------------------------------------------------------

The first milestone can run the generator and validation pipeline from
the command line without a frontend. Build the dashboard only after the
underlying calculations pass tests.

### 3.2 Logical flow

``` text
Versioned configuration + fixed seed
                |
                v
       Synthetic data generator
                |
                v
  Master tables -> child/event tables
                |
                v
    Relational database / raw files
                |
                v
      Integrity and quality checks
                |
                v
       Customer journey reconstruction
                |
                v
       Attribution calculation engine
                |
                v
   Cost/revenue reconciliation and ROI
                |
                v
       Exception detection + ground truth
                |
                v
 Exports, run manifest, validation report, API
                |
                v
          Analytics dashboard
```

### 3.3 Data layers

-   **Raw/source layer:** generated records as supplied by the
    generator. Do not silently repair or overwrite source rows.
-   **Validated layer:** records and relationships that passed
    structural checks, plus explicit validation findings.
-   **Analytics layer:** reconstructed journeys, attribution results,
    campaign metrics and ROI.
-   **Evaluation layer:** ground truth and evaluation results. Keep
    ground truth out of the detection inputs.
-   **Audit layer:** generation runs, state-change events, issue records
    and calculation versions.

------------------------------------------------------------------------

## 4. Repository Structure

Recommended starting layout:

``` text
marketing-attribution/
├── README.md
├── IMPLEMENTATION_PLAN.md
├── pyproject.toml
├── .env.example
├── config/
│   ├── starter.yaml
│   └── full.yaml
├── docs/
│   ├── architecture.md
│   ├── data_dictionary.md
│   ├── schema.md
│   ├── attribution_rules.md
│   ├── validation_rules.md
│   └── source_manifest.md
├── src/
│   └── attribution/
│       ├── config.py
│       ├── ids.py
│       ├── generator/
│       │   ├── master_data.py
│       │   ├── contacts.py
│       │   ├── touchpoints.py
│       │   ├── web_sessions.py
│       │   ├── leads.py
│       │   ├── opportunities.py
│       │   ├── orders.py
│       │   ├── costs.py
│       │   └── anomalies.py
│       ├── db/
│       │   ├── models.py
│       │   ├── session.py
│       │   └── repositories.py
│       ├── pipeline/
│       │   ├── validate.py
│       │   ├── journeys.py
│       │   ├── attribution.py
│       │   ├── reconciliation.py
│       │   ├── exceptions.py
│       │   └── metrics.py
│       ├── export/
│       │   ├── csv_export.py
│       │   ├── json_export.py
│       │   ├── sql_export.py
│       │   └── checksums.py
│       └── api/
│           ├── main.py
│           └── routes/
├── frontend/
│   └── ...
├── sql/
│   ├── schema.sql
│   └── seed.sql
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── acceptance/
│   └── reproducibility/
├── data/
│   ├── generated/
│   ├── ground_truth/
│   └── reports/
└── scripts/
    ├── generate_data.py
    ├── run_pipeline.py
    ├── validate_data.py
    └── verify_reproducibility.py
```

Generated files should be written to a run-specific directory, for
example `data/generated/run_<run_id>/`, to avoid accidental overwrites.
The reproducibility comparison should compare normalized data outputs,
not volatile run timestamps.

------------------------------------------------------------------------

## 5. Data Model and Relationship Design

### 5.1 Conventions

-   Use immutable string IDs following the requested naming patterns.
-   Store timestamps in UTC in the database; document the source
    timezone when generated timestamps are created.
-   Use `TIMESTAMPTZ` for timestamps and `DATE` for date-only fields.
-   Use `NUMERIC(18,2)` for money and `NUMERIC(9,6)` or an equivalent
    decimal type for attribution shares.
-   Store ISO currency codes such as `INR`, `USD`, `AUD` in a
    three-character field.
-   Use controlled enums or check constraints for statuses and event
    types.
-   Store source timestamps and original currency/amount. Never replace
    them with converted values without preserving the original.
-   Use foreign keys for all required relationships. Optional
    relationships may be null but must have documented reasons.
-   Use `created_at` and `updated_at` for operational metadata where
    useful, but do not treat `updated_at` as a substitute for event
    history.
-   Store calculation version and rule version on derived outputs.
-   Use database indexes on foreign keys and common filter/join columns,
    especially timestamps, campaign IDs, contact IDs and order IDs.

### 5.2 Entity relationship summary

  ------------------------------------------------------------------------------
  Parent            Child / bridge      Cardinality       Relationship rules
  ----------------- ------------------- ----------------- ----------------------
  Channel           Campaign            1:N               Each campaign has one
                                                          primary channel in v1;
                                                          use a campaign-channel
                                                          bridge if multiple
                                                          channels per campaign
                                                          are required

  Campaign          Touchpoint          1:N               A touchpoint refers to
                                                          one campaign when
                                                          campaign-attributed;
                                                          campaign can be
                                                          nullable only for
                                                          explicitly
                                                          unattributed events

  Contact           Touchpoint          1:N               A touchpoint may have
                                                          no contact when
                                                          anonymous; anonymous
                                                          identity must not be
                                                          guessed

  Contact           WebSession          1:N               Session contact is
                                                          optional until
                                                          identity is supported
                                                          by evidence

  WebSession        Lead                1:N or 1:0..1     Define whether a
                                                          session can create
                                                          multiple leads; v1 may
                                                          allow at most one
                                                          primary lead per
                                                          session

  Contact           Lead                1:N               A lead normally
                                                          references a contact;
                                                          define an explicit
                                                          anonymous-lead policy
                                                          if allowed

  Lead              Opportunity         1:N               A lead may create
                                                          multiple opportunities

  Opportunity       Order               1:N               Supports
                                                          split/multiple orders;
                                                          each order must have a
                                                          unique economic
                                                          transaction identity

  Campaign          CostRecord          1:N               Each cost record
                                                          belongs to one
                                                          campaign unless a
                                                          documented shared-cost
                                                          allocation model is
                                                          introduced

  Order             AttributionResult   1:N               One result per
                                                          eligible campaign per
                                                          order per
                                                          model/version

  Campaign          AttributionResult   1:N               A campaign may receive
                                                          credit for many orders

  Campaign          Creative            N:M (via bridge)  A campaign can use
                                                          multiple creatives; a
                                                          creative can be reused
                                                          by campaigns

  Campaign          Audience            N:M (via bridge)  A campaign can target
                                                          multiple audiences; an
                                                          audience can be reused

  Opportunity       OpportunityEvent    1:N               Append lifecycle
                                                          transitions; do not
                                                          overwrite event
                                                          history

  Order             OrderEvent          1:N               Append order state
                                                          changes, refunds and
                                                          corrections

  Pipeline run      ValidationResult /  1:N               Record checks and
                    Issue                                 issue findings per run
  ------------------------------------------------------------------------------

The exact cardinalities must be documented and enforced. Where a
relationship is optional, document the reason and how the record is
treated by attribution.

### 5.3 Table-by-table data dictionary

The field lists below are the minimum v1 contract. `PK` means primary
key, `FK` means foreign key. Add `created_at` where operationally
useful. Enforce constraints in both application validation and, where
possible, the database.

#### A. `channel`

  --------------------------------------------------------------------------
  Field            Type                          Required Rules
  ---------------- ---------------- --------------------- ------------------
  `channel_id`     VARCHAR(32)                    Yes, PK Immutable, unique;
                                                          e.g. `CH-000001`

  `name`           VARCHAR(80)                        Yes Unique normalized
                                                          name

  `channel_type`   VARCHAR(30)                        Yes Enum:
                                                          `PAID_SEARCH`,
                                                          `PAID_SOCIAL`,
                                                          `EMAIL`,
                                                          `ORGANIC`,
                                                          `REFERRAL`,
                                                          `OFFLINE`,
                                                          `DISPLAY`, `OTHER`

  `is_active`      BOOLEAN                            Yes Defaults true

  `created_at`     TIMESTAMPTZ                        Yes Valid timestamp
  --------------------------------------------------------------------------

#### B. `campaign`

  -------------------------------------------------------------------------------
  Field             Type                          Required Rules
  ----------------- ---------------- --------------------- ----------------------
  `campaign_id`     VARCHAR(32)                    Yes, PK `CMP-2026-000001`
                                                           pattern; immutable

  `name`            VARCHAR(160)                       Yes Non-empty

  `channel_id`      VARCHAR(32)                    Yes, FK References
                                                           `channel.channel_id`

  `budget_amount`   NUMERIC(18,2)                      Yes `>= 0`; planned
                                                           budget, not actual
                                                           cost

  `currency`        CHAR(3)                            Yes ISO-style code;
                                                           e.g. `INR`, `USD`,
                                                           `AUD`

  `start_at`        TIMESTAMPTZ                        Yes Must be \<= `end_at`

  `end_at`          TIMESTAMPTZ                        Yes Must be \>= `start_at`

  `status`          VARCHAR(20)                        Yes `DRAFT`, `PLANNED`,
                                                           `ACTIVE`, `PAUSED`,
                                                           `COMPLETED`,
                                                           `CANCELLED`

  `objective`       VARCHAR(80)                         No Controlled or
                                                           documented free-text
                                                           category

  `created_at`      TIMESTAMPTZ                        Yes Valid timestamp
  -------------------------------------------------------------------------------

#### C. `creative`

  --------------------------------------------------------------------------
  Field             Type                          Required Rules
  ----------------- ---------------- --------------------- -----------------
  `creative_id`     VARCHAR(32)                    Yes, PK Unique, immutable

  `name`            VARCHAR(120)                       Yes Non-empty

  `format`          VARCHAR(30)                        Yes `TEXT`, `IMAGE`,
                                                           `VIDEO`,
                                                           `LANDING_PAGE`,
                                                           `BANNER`, `OTHER`

  `version`         VARCHAR(30)                        Yes Non-empty version
                                                           label

  `active_from`     TIMESTAMPTZ                        Yes \<= `active_to`
                                                           when end exists

  `active_to`       TIMESTAMPTZ                         No Null means no
                                                           known end

  `metadata_json`   JSONB                               No Synthetic,
                                                           non-sensitive
                                                           metadata only
  --------------------------------------------------------------------------

#### D. `audience`

  ----------------------------------------------------------------------------
  Field              Type                          Required Rules
  ------------------ ---------------- --------------------- ------------------
  `audience_id`      VARCHAR(32)                    Yes, PK Unique, immutable

  `name`             VARCHAR(120)                       Yes Non-empty

  `segment_type`     VARCHAR(40)                        Yes `NEW`,
                                                            `RETURNING`,
                                                            `HIGH_INTENT`,
                                                            `GENERAL`,
                                                            `BUSINESS`,
                                                            `OTHER`

  `criteria_json`    JSONB                               No Synthetic
                                                            documented
                                                            criteria; no
                                                            sensitive personal
                                                            attributes

  `effective_from`   TIMESTAMPTZ                        Yes Valid timestamp

  `effective_to`     TIMESTAMPTZ                         No Must be \>=
                                                            `effective_from`
  ----------------------------------------------------------------------------

#### E. `contact`

  -------------------------------------------------------------------------------
  Field                Type                          Required Rules
  -------------------- ---------------- --------------------- -------------------
  `contact_id`         VARCHAR(32)                    Yes, PK Stable synthetic
                                                              ID,
                                                              e.g. `CON-000001`

  `created_at`         TIMESTAMPTZ                        Yes Valid timestamp

  `region`             VARCHAR(40)                         No Synthetic region
                                                              label

  `customer_segment`   VARCHAR(40)                         No Controlled
                                                              synthetic segment

  `consent_status`     VARCHAR(20)                        Yes `UNKNOWN`,
                                                              `GRANTED`,
                                                              `DENIED`,
                                                              `WITHDRAWN`;
                                                              synthetic only

  `is_synthetic`       BOOLEAN                            Yes Must be true for
                                                              this dataset

  `identity_status`    VARCHAR(20)                        Yes `KNOWN`, `PARTIAL`,
                                                              `UNRESOLVED`
  -------------------------------------------------------------------------------

Do not generate real names, real emails, real phone numbers or other
identifying personal data unless there is a specific lawful need.
Synthetic IDs and non-identifying attributes are sufficient for this
project.

#### F. `campaign_creative` bridge

  Field              Type              Required Rules
  ------------------ ------------- ------------ ----------------------
  `campaign_id`      VARCHAR(32)     Yes, PK/FK References campaign
  `creative_id`      VARCHAR(32)     Yes, PK/FK References creative
  `effective_from`   TIMESTAMPTZ            Yes Effective start
  `effective_to`     TIMESTAMPTZ             No \>= start if present

Composite primary key: (`campaign_id`, `creative_id`, `effective_from`)
if creatives can be reassigned over time; otherwise use (`campaign_id`,
`creative_id`).

#### G. `campaign_audience` bridge

  Field              Type              Required Rules
  ------------------ ------------- ------------ ----------------------
  `campaign_id`      VARCHAR(32)     Yes, PK/FK References campaign
  `audience_id`      VARCHAR(32)     Yes, PK/FK References audience
  `effective_from`   TIMESTAMPTZ            Yes Effective start
  `effective_to`     TIMESTAMPTZ             No \>= start if present

Use a composite key that includes the effective start when assignments
can change over time.

#### H. `touchpoint`

  -------------------------------------------------------------------------------------------
  Field                 Type                          Required Rules
  --------------------- ---------------- --------------------- ------------------------------
  `touchpoint_id`       VARCHAR(80)                    Yes, PK `TOUCH-<contact-id>-000001`;
                                                               use a documented anonymous
                                                               variant when no contact exists

  `contact_id`          VARCHAR(32)             Conditional FK Nullable only for
                                                               anonymous/unresolved events

  `campaign_id`         VARCHAR(32)             Conditional FK Nullable only for explicitly
                                                               unattributed touchpoints

  `channel_id`          VARCHAR(32)                    Yes, FK References channel

  `creative_id`         VARCHAR(32)                     No, FK Must be valid at event time if
                                                               supplied

  `occurred_at`         TIMESTAMPTZ                        Yes Valid timestamp; can be after
                                                               a conversion only as a
                                                               deliberate test case

  `touch_type`          VARCHAR(30)                        Yes `IMPRESSION`, `CLICK`,
                                                               `EMAIL_OPEN`, `EMAIL_CLICK`,
                                                               `FORM_SUBMIT`, `PHONE_CALL`,
                                                               `EVENT_ATTENDANCE`,
                                                               `SALES_TOUCH`, `OTHER`

  `touch_mode`          VARCHAR(12)                        Yes `ONLINE`, `OFFLINE`

  `source_event_id`     VARCHAR(80)                         No Unique where supplied;
                                                               supports deduplication

  `identity_evidence`   VARCHAR(30)                        Yes `AUTHENTICATED`,
                                                               `CONSENTED_MATCH`,
                                                               `SESSION_LINK`, `NONE`,
                                                               `UNKNOWN`

  `issue_type`          VARCHAR(50)                         No Populated for deliberately
                                                               injected/identified anomalies

  `is_synthetic`        BOOLEAN                            Yes True
  -------------------------------------------------------------------------------------------

Touchpoint IDs use a counter scoped to contact. Define the exact
anonymous ID format in `ids.py`; never invent a contact ID to fill a
null.

#### I. `web_session`

  ----------------------------------------------------------------------------------
  Field                 Type                          Required Rules
  --------------------- ---------------- --------------------- ---------------------
  `session_id`          VARCHAR(32)                    Yes, PK `SES-2026-000001`
                                                               pattern

  `contact_id`          VARCHAR(32)                     No, FK Null for anonymous
                                                               sessions unless
                                                               identity evidence
                                                               supports linking

  `campaign_id`         VARCHAR(32)                     No, FK Campaign associated
                                                               through verified
                                                               UTM/referral data

  `started_at`          TIMESTAMPTZ                        Yes Valid timestamp

  `ended_at`            TIMESTAMPTZ                         No \>= start if present

  `source_channel_id`   VARCHAR(32)                     No, FK References channel

  `landing_path`        VARCHAR(200)                        No Synthetic route/path,
                                                               not a real user's URL

  `identity_evidence`   VARCHAR(30)                        Yes Same documented
                                                               evidence categories
                                                               as above

  `is_anonymous`        BOOLEAN                            Yes If true, contact must
                                                               be null unless a
                                                               separate, later
                                                               identity-resolution
                                                               event is recorded

  `issue_type`          VARCHAR(50)                         No For known test cases
  ----------------------------------------------------------------------------------

#### J. `lead`

  --------------------------------------------------------------------------------
  Field                Type                          Required Rules
  -------------------- ---------------- --------------------- --------------------
  `lead_id`            VARCHAR(32)                    Yes, PK `LEAD-2026-000001`
                                                              pattern

  `contact_id`         VARCHAR(32)                    Yes, FK References contact
                                                              in v1

  `session_id`         VARCHAR(32)                     No, FK Must exist if
                                                              supplied

  `created_at`         TIMESTAMPTZ                        Yes Valid timestamp

  `status`             VARCHAR(20)                        Yes `NEW`, `QUALIFIED`,
                                                              `DISQUALIFIED`,
                                                              `CONVERTED`,
                                                              `CLOSED`

  `source_type`        VARCHAR(20)                        Yes `WEB`, `OFFLINE`,
                                                              `REFERRAL`, `SALES`,
                                                              `OTHER`

  `qualification_at`   TIMESTAMPTZ                         No Must be \>= lead
                                                              creation

  `issue_type`         VARCHAR(50)                         No Explicit issue label
                                                              only
  --------------------------------------------------------------------------------

#### K. `opportunity`

  ----------------------------------------------------------------------------------
  Field                   Type                          Required Rules
  ----------------------- ---------------- --------------------- -------------------
  `opportunity_id`        VARCHAR(32)                    Yes, PK `OPP-2026-000001`
                                                                 pattern

  `lead_id`               VARCHAR(32)                    Yes, FK References lead

  `created_at`            TIMESTAMPTZ                        Yes Must be \>= lead
                                                                 creation under v1
                                                                 rule

  `expected_value`        NUMERIC(18,2)                      Yes \>= 0

  `currency`              CHAR(3)                            Yes ISO-style code

  `status`                VARCHAR(20)                        Yes `OPEN`,
                                                                 `QUALIFIED`,
                                                                 `PROPOSAL`, `WON`,
                                                                 `LOST`, `CANCELLED`

  `closed_at`             TIMESTAMPTZ                         No Required for `WON`
                                                                 or `LOST`; \>=
                                                                 creation

  `actual_closed_value`   NUMERIC(18,2)                       No \>= 0; required for
                                                                 a won opportunity
                                                                 if business rules
                                                                 require a known
                                                                 value

  `issue_type`            VARCHAR(50)                         No Explicit anomaly
                                                                 label
  ----------------------------------------------------------------------------------

The requested 10,000 opportunity count is the target total, not the
number of won opportunities. A realistic mix of open, won, lost and
cancelled states is required.

#### L. `order`

  -----------------------------------------------------------------------------------------------------
  Field                        Type                          Required Rules
  ---------------------------- ---------------- --------------------- ---------------------------------
  `order_id`                   VARCHAR(32)                    Yes, PK `ORD-2026-000001` pattern

  `opportunity_id`             VARCHAR(32)                     No, FK Optional for orders outside the
                                                                      opportunity process; document
                                                                      policy

  `contact_id`                 VARCHAR(32)                    Yes, FK References purchaser/contact

  `ordered_at`                 TIMESTAMPTZ                        Yes Valid timestamp

  `status`                     VARCHAR(20)                        Yes `PENDING`, `PAID`, `REFUNDED`,
                                                                      `PARTIALLY_REFUNDED`, `CANCELLED`

  `gross_amount`               NUMERIC(18,2)                      Yes \>= 0

  `refund_amount`              NUMERIC(18,2)                      Yes \>= 0 and \<= gross amount

  `net_revenue`                NUMERIC(18,2)                  Derived `gross_amount - refund_amount`;
                                                                      calculate, do not independently
                                                                      randomize

  `currency`                   CHAR(3)                            Yes ISO-style code

  `economic_transaction_key`   VARCHAR(80)                        Yes Identifies the underlying
                                                                      economic transaction; unique for
                                                                      valid transactions, duplicated
                                                                      only in labelled anomaly fixtures

  `issue_type`                 VARCHAR(50)                         No For deliberately injected
                                                                      duplicate or other issue
  -----------------------------------------------------------------------------------------------------

Use `net_revenue` as the revenue basis if the documented policy is net
of refunds. Choose and document a single consistent policy.

#### M. `cost_record`

  -----------------------------------------------------------------------------------------------
  Field                          Type                          Required Rules
  ------------------------------ ---------------- --------------------- -------------------------
  `cost_record_id`               VARCHAR(32)                    Yes, PK `COST-2026-000001`
                                                                        pattern

  `campaign_id`                  VARCHAR(32)                    Yes, FK References campaign

  `incurred_at`                  TIMESTAMPTZ                        Yes Valid timestamp

  `cost_type`                    VARCHAR(30)                        Yes `MEDIA`, `AGENCY`,
                                                                        `PRODUCTION`, `PLATFORM`,
                                                                        `OTHER`

  `amount`                       NUMERIC(18,2)                      Yes \>= 0

  `currency`                     CHAR(3)                            Yes ISO-style code

  `exchange_rate_to_reporting`   NUMERIC(18,8)              Conditional Required if conversion is
                                                                        used; positive

  `reporting_amount`             NUMERIC(18,2)                  Derived Calculated from amount
                                                                        and documented
                                                                        exchange-rate policy

  `rate_date`                    DATE                       Conditional Required when exchange
                                                                        rate is applied

  `source_reference`             VARCHAR(80)                         No Synthetic invoice/expense
                                                                        reference

  `issue_type`                   VARCHAR(50)                         No E.g. `CURRENCY_MISMATCH`,
                                                                        `MISSING_COST_EXPECTED`
  -----------------------------------------------------------------------------------------------

A missing-cost anomaly is usually represented by an expected-cost
finding or campaign-level completeness check, not by inserting a fake
cost amount of zero.

#### N. `attribution_result`

  -------------------------------------------------------------------------------------------------
  Field                       Type                          Required Rules
  --------------------------- ---------------- --------------------- ------------------------------
  `attribution_result_id`     VARCHAR(40)                    Yes, PK Deterministic ID based on
                                                                     order/model/campaign/version
                                                                     or stable counter

  `order_id`                  VARCHAR(32)                    Yes, FK References order

  `campaign_id`               VARCHAR(32)             Conditional FK Null only for an explicit
                                                                     unattributed bucket if that is
                                                                     the chosen schema

  `model_name`                VARCHAR(30)                        Yes `FIRST_TOUCH`, `LAST_TOUCH`,
                                                                     `LINEAR`

  `model_version`             VARCHAR(20)                        Yes Versioned rule set

  `credit_share`              NUMERIC(9,6)                       Yes Between 0 and 1

  `attributed_revenue`        NUMERIC(18,2)                      Yes Derived from eligible order
                                                                     revenue and share, with
                                                                     documented rounding

  `eligible_touchpoint_ids`   JSONB or bridge                    Yes Prefer an
                                                                     `attribution_touchpoint`
                                                                     bridge for normalized
                                                                     traceability

  `calculated_at`             TIMESTAMPTZ                        Yes Calculation timestamp

  `decision_reason`           VARCHAR(200)                        No Explanation for
                                                                     attribution/exclusion

  `run_id`                    VARCHAR(40)                        Yes Links to pipeline run

  `issue_type`                VARCHAR(50)                         No Issue association when
                                                                     applicable
  -------------------------------------------------------------------------------------------------

Recommended normalized bridge:
`attribution_touchpoint(attribution_result_id, touchpoint_id, contribution_weight)`
with foreign keys. This avoids storing a list of IDs only in JSON.

#### O. Event history tables

Create at minimum:

**`opportunity_event`** - `opportunity_event_id` PK - `opportunity_id`
FK - `event_type` - `old_status` nullable - `new_status` nullable -
`occurred_at` - `event_payload` JSONB, optional - `run_id`

**`order_event`** - `order_event_id` PK - `order_id` FK - `event_type`
such as `CREATED`, `PAID`, `REFUNDED`, `CANCELLED`, `CORRECTED` -
`old_status`, `new_status` - `occurred_at` - `event_payload` JSONB,
optional - `run_id`

Append events rather than editing historical event rows. If a
current-state table is maintained, update it transactionally while
retaining the event.

#### P. Run, issue and validation tables

**`pipeline_run`** - `run_id` PK - `started_at`, `completed_at` -
`seed` - `generator_version` - `config_hash` - `dataset_scale` -
`status` - `row_counts_json` - `checksums_json`

**`data_issue`** - `issue_id` PK - `run_id` FK - `entity_type` -
`entity_id` - `issue_type` - `severity` (`INFO`, `LOW`, `MEDIUM`,
`HIGH`, `CRITICAL`) - `detected_at` - `decision` - `resolution_status`
(`OPEN`, `ACKNOWLEDGED`, `RESOLVED`, `ACCEPTED`) - `details_json`

**`validation_result`** - `validation_result_id` PK - `run_id` FK -
`check_name` - `entity_name` - `records_checked` - `failure_count` -
`status` - `details_json` - `executed_at`

------------------------------------------------------------------------

## 6. ID and Naming Strategy

Use a central ID module. IDs must be deterministic, zero-padded and
immutable.

  ----------------------------------------------------------------------------------------
  Entity                  Format                               Example
  ----------------------- ------------------------------------ ---------------------------
  Campaign                `CMP-2026-{counter:06d}`             `CMP-2026-000001`

  Contact                 `CON-{counter:06d}`                  `CON-000001`

  Touchpoint              `TOUCH-{contact-id}-{counter:06d}`   `TOUCH-CON-000001-000001`

  Session                 `SES-2026-{counter:06d}`             `SES-2026-000001`

  Lead                    `LEAD-2026-{counter:06d}`            `LEAD-2026-000001`

  Opportunity             `OPP-2026-{counter:06d}`             `OPP-2026-000001`

  Order                   `ORD-2026-{counter:06d}`             `ORD-2026-000001`

  Cost                    `COST-2026-{counter:06d}`            `COST-2026-000001`

  Channel                 `CH-{counter:06d}`                   `CH-000001`

  Creative                `CRE-{counter:06d}`                  `CRE-000001`

  Audience                `AUD-{counter:06d}`                  `AUD-000001`
  ----------------------------------------------------------------------------------------

The brief's touchpoint pattern uses `<contact-id>`. Define whether the
embedded value is the full contact ID or its numeric suffix and use one
convention everywhere. The example above embeds the full ID. Use an
explicitly documented anonymous-touchpoint format when `contact_id` is
null.

Never derive IDs from random values or timestamps. Use stable counters
and stable iteration order.

------------------------------------------------------------------------

## 7. Synthetic Data Generation Strategy

### 7.1 Configuration

Use a version-controlled configuration file with fields such as:

``` yaml
seed: 20261022
dataset_scale: starter
reporting_currency: INR
counts:
  campaigns: 25
  contacts: 1000
  touchpoints: 4000
  opportunities: 200
conversion_window_days: 180
anomaly_injection_enabled: true
anomaly_rates:
  duplicate_revenue: 0.002
  post_conversion_touch: 0.002
  currency_mismatch: 0.002
  missing_campaign_cost: 0.002
  unsupported_identity_link: 0.002
```

The rates above are illustrative defaults for development, not
requirements from the problem statement. Choose and document rates that
result in enough cases for testing. Use a separate full configuration
with 500 campaigns, 50,000 contacts, 200,000 touchpoints and 10,000
opportunities. Keep all generation logic the same between starter and
full modes.

### 7.2 Generation order

1.  Create channels.
2.  Create creatives and audiences.
3.  Create campaigns with channel, budget, currency, effective dates and
    lifecycle status.
4.  Create campaign-creative and campaign-audience bridge rows.
5.  Create contacts.
6.  Generate touchpoints against existing campaigns, channels, contacts
    and creatives.
7.  Generate web sessions and evidence-supported identity links.
8.  Generate leads from qualifying events/sessions or documented offline
    lead sources.
9.  Generate opportunities from valid leads.
10. Generate won/lost/open lifecycle events.
11. Generate orders from valid conversion outcomes under the chosen
    business policy.
12. Generate cost records across campaign dates.
13. Calculate derived amounts and statuses from source facts.
14. Validate the clean baseline.
15. Inject labelled anomaly fixtures.
16. Re-run validation and produce issue findings.
17. Calculate attribution and ROI using source data and the selected
    anomaly-handling policies.
18. Export entity files, ground truth, checksums and reports.

### 7.3 Realism requirements

Do not distribute every field uniformly. Use documented distributions
such as: - Campaign budgets vary by channel and objective. - Touchpoint
counts per contact follow a skewed distribution; many contacts have few
touches, while a smaller group have long journeys. - Campaigns vary in
duration and may overlap. - Some journeys include multiple campaigns and
channels. - Touches can be online or offline. - Lead conversion and
opportunity win rates are non-uniform. - Conversion delays vary,
including long windows. - Some sessions remain anonymous or
unresolved. - Cost records can be periodic (e.g. daily/weekly) or
event-based, but use one documented approach. - Dates must respect
effective dates except in specifically labelled anomaly fixtures.

All these are synthetic distributions. Document the choices in the
README; do not claim they are observed industry benchmarks unless
supported by a licensed public source.

### 7.4 Derived values

Calculate rather than independently randomize: - Campaign actual cost =
sum of included valid cost records after currency normalization. - Order
net revenue = gross amount minus refunds, under the chosen policy. -
Opportunity close duration = close timestamp minus creation timestamp. -
Attribution share = output of the selected attribution rule. -
Attributed revenue = eligible order revenue × share, rounded with a
reconciliation rule. - ROI =
`(attributed_revenue - normalized_cost) / normalized_cost * 100`, only
if valid cost is positive and complete. - Conversion status from
lifecycle events and business rules. - Data-quality status from
validation findings.

### 7.5 Anomaly injection

Generate clean baseline data first. Then inject controlled, identifiable
anomalies into dedicated fixture records or clearly labelled generated
rows. Keep unrelated rows valid.

1.  **Duplicate revenue:** Create two records that point to the same
    `economic_transaction_key` or otherwise represent the same economic
    transaction. Expected result: identify the duplicate and count the
    underlying transaction only once.
2.  **Post-conversion touchpoint:** Add a touch after the
    order/conversion timestamp and ensure it is not eligible for that
    conversion.
3.  **Currency mismatch:** Create a cost record in a currency different
    from the reporting currency and test conversion using a dated rate
    or flagging behavior if no valid rate exists.
4.  **Missing costs:** Designate a campaign whose expected cost coverage
    is incomplete. Do not substitute a zero cost. Expected result: ROI
    is unavailable or explicitly provisional.
5.  **Unsupported anonymous identity:** Create an anonymous session with
    a contact link that has no valid evidence. Expected result: flag or
    quarantine the link, preserve the source record, and do not treat it
    as a trusted journey join.

Each injected case must have an `issue_type`, a stable issue/entity
reference and a ground-truth label. Ground truth must be stored
separately from the features/records used by the detection logic.

------------------------------------------------------------------------

## 8. Attribution Rules

Create `docs/attribution_rules.md` and version every rule set. Use the
same rules in code, tests and documentation.

### 8.1 Common eligibility rules

A touchpoint is eligible for an order only if: 1. It occurred at or
before the conversion timestamp. 2. It falls within the configured
lookback/conversion window. 3. It has a valid campaign reference or is
explicitly classified as unattributed. 4. It belongs to the order's
supported customer journey under the identity policy. 5. It passes
deduplication and any documented touch-type eligibility rule. 6. It was
effective/active according to the campaign and creative rules where
applicable.

Do not require a campaign to have been active at touch time unless the
campaign lifecycle policy says so; if it was inactive, flag or exclude
it according to the documented rule. Use event timestamps, not file row
order.

### 8.2 First-touch

-   Sort eligible touchpoints by `occurred_at`, then stable
    `touchpoint_id` as a tie-breaker.
-   Assign 100% credit to the earliest eligible touchpoint's campaign.
-   If no eligible touchpoint exists, create an explicit unattributed
    outcome or mark the order as unattributed.
-   Store the chosen touchpoint and the rule version.

### 8.3 Last-touch

-   Use the same eligibility rules.
-   Assign 100% credit to the latest eligible touchpoint before or at
    conversion.
-   Use a deterministic tie-breaker for identical timestamps.
-   Never attribute a conversion to a touchpoint after conversion.

### 8.4 Linear multi-touch

-   Let `n` be the number of eligible touchpoints or distinct eligible
    campaigns. Choose one policy and state it explicitly.
-   Recommended v1 policy: split equally across distinct eligible
    campaigns so repeated clicks from one campaign do not automatically
    gain more credit solely because of event volume.
-   Credit share per eligible campaign is `1/n`.
-   If the business instead wants equal credit per touchpoint, implement
    it as a separately named model; do not silently mix these
    interpretations.
-   Use decimal arithmetic and allocate rounding remainder
    deterministically so total attributed revenue equals the eligible
    order revenue to the cent.

### 8.5 Conversion windows and evaluation split

-   Default v1 lookback window: 180 days, configurable.
-   Define how the conversion timestamp is selected (e.g. paid order
    timestamp; not opportunity creation time).
-   Use chronological train/validation/test periods, not a random row
    split.
-   Document how long conversion windows crossing a split boundary are
    handled.
-   Avoid leakage: features for a conversion must not include future
    touchpoints.
-   Keep an explicit `evaluation_period` or derive it using documented
    cut-off dates.
-   Include a maturity/censoring policy for conversions whose full
    lookback window has not elapsed by the end of the dataset.

------------------------------------------------------------------------

## 9. Cost, Revenue and ROI Rules

### 9.1 Revenue policy

Recommended v1: - Count a paid order's net revenue once. - Exclude
cancelled orders. - Subtract recorded refunds. - Do not sum duplicate
records representing the same economic transaction. - Keep duplicate
source rows visible as issues. - State whether revenue is reported on
order date or attribution/conversion date; use the same rule in all
model comparisons.

### 9.2 Currency policy

-   Select one reporting currency in configuration, e.g. `INR`.
-   Preserve source amount and currency.
-   Store the exchange rate, rate date, source/reference and converted
    amount when converting.
-   Use a documented rate source or synthetic exchange-rate table for
    fully synthetic data.
-   Do not sum different currencies directly.
-   If no valid rate is available, mark the financial aggregate as
    incomplete and ROI as unavailable.

### 9.3 Campaign cost policy

-   Actual cost is derived from valid cost records, not from campaign
    budget.
-   A campaign budget is a plan/limit, not a substitute for actual
    spend.
-   Define expected cost coverage: for example, a campaign may require
    cost records for its active period, or a known cost source may be
    marked complete.
-   Missing cost coverage must be represented as an exception, not zero
    spend.
-   For cost = 0, ROI is undefined; do not divide by zero or report
    infinity.
-   When cost is incomplete or currency conversion fails, return an
    explicit status such as `INCOMPLETE_COST` or `CURRENCY_UNRESOLVED`.

### 9.4 Reconciliation

For every order with valid attribution: - Sum of attribution shares
across campaigns must equal 1.0 (within a documented decimal
tolerance). - Sum of attributed revenue across campaigns must equal the
order's eligible net revenue to the cent. - Across all orders,
campaign-attributed revenue plus unattributed revenue must reconcile to
eligible total revenue. - Do not sum the full order revenue once for
each campaign touched. - Produce a reconciliation report with expected
amount, calculated amount, difference and pass/fail status.

------------------------------------------------------------------------

## 10. Ground Truth and Evaluation Design

### 10.1 Ground-truth file

Create `data/ground_truth/ground_truth.csv` or JSON. Suggested fields:

  -----------------------------------------------------------------------
  Field                               Meaning
  ----------------------------------- -----------------------------------
  `ground_truth_id`                   Stable unique label ID

  `entity_type`                       Entity containing the known case

  `entity_id`                         Stable reference to affected record

  `issue_type`                        Expected anomaly category

  `expected_detection`                Whether a detector should flag it

  `expected_decision`                 Expected handling, e.g. exclude
                                      touch or block ROI

  `severity`                          Expected issue severity

  `rule_id`                           Rule being tested

  `notes`                             Human-readable rationale
  -----------------------------------------------------------------------

Do not include ground-truth labels in the detector's input feature set
or use them to make the detection decision. They are only for test
assertions and evaluation.

### 10.2 Evaluation metrics

Report at least: - Primary-key duplicate count. - Foreign-key failure
count. - Date-order failure count. - Invalid enum count. - Financial
reconciliation difference. - Attribution share reconciliation pass
rate. - Attribution coverage = conversions with eligible attribution /
eligible conversions. - Identity resolution rate = sessions with
evidence-supported identity / sessions eligible for resolution. -
Exception precision = true positive detections / all positive
detections. - Exception recall = true positive detections / all
ground-truth positive cases. - Exception F1 score, if precision and
recall are defined. - ROI availability rate = campaigns with
sufficiently complete costs / campaigns requiring cost reporting. -
Reproducibility result and checksum comparison.

For metrics that use a denominator of zero, report `N/A`, not zero or
infinity. State denominators and exclusions next to every metric.

### 10.3 Chronological evaluation

Define dates based on the generated time range. Example only: -
Train/development: earliest 60% of time range. - Validation: next 20%. -
Test: final 20%.

The final periods should be date-based and non-overlapping. Do not
randomly split events from the same journey across periods without a
documented policy. Use the ground truth only to score the detector,
never as an input.

------------------------------------------------------------------------

## 11. API Design (if building a web application)

Recommended first-version endpoints:

  --------------------------------------------------------------------------------------
  Method                  Endpoint                               Purpose
  ----------------------- -------------------------------------- -----------------------
  `GET`                   `/health`                              API health check

  `POST`                  `/api/runs`                            Start a configured
                                                                 generation/pipeline run

  `GET`                   `/api/runs/{run_id}`                   Run status and counts

  `GET`                   `/api/runs/{run_id}/validation`        Validation summary

  `GET`                   `/api/campaigns`                       Paginated campaign list
                                                                 with filters

  `GET`                   `/api/campaigns/{campaign_id}`         Campaign detail and
                                                                 cost/revenue metrics

  `GET`                   `/api/campaigns/{campaign_id}/roi`     ROI and reconciliation
                                                                 detail

  `GET`                   `/api/attribution/compare`             Compare models for
                                                                 selected date range

  `GET`                   `/api/orders/{order_id}/attribution`   Attribution results and
                                                                 traceability

  `GET`                   `/api/contacts/{contact_id}/journey`   Chronological customer
                                                                 journey

  `GET`                   `/api/issues`                          Filterable exception
                                                                 list

  `GET`                   `/api/issues/{issue_id}`               Issue detail and
                                                                 affected records

  `GET`                   `/api/metrics`                         Overall evaluation
                                                                 metrics

  `GET`                   `/api/exports/{run_id}`                List available exports
                                                                 for a run
  --------------------------------------------------------------------------------------

API requirements: - Validate query parameters and request bodies with
Pydantic. - Use pagination for large tables. - Return explicit status
fields for unavailable ROI or incomplete attribution. - Do not return
ground-truth labels through normal operational endpoints. - Protect
run-triggering endpoints if exposed beyond local development. - Use
stable error shapes and appropriate HTTP status codes. - Keep
long-running generation jobs separate from normal request-response
handling if needed.

Example comparison response shape:

``` json
{
  "reporting_currency": "INR",
  "period": {"start": "2026-01-01", "end": "2026-10-31"},
  "models": [
    {
      "model": "FIRST_TOUCH",
      "attributed_revenue": 1250000.00,
      "roi_percent": 42.5,
      "reconciliation_status": "PASS"
    },
    {
      "model": "LAST_TOUCH",
      "attributed_revenue": 1250000.00,
      "roi_percent": 38.2,
      "reconciliation_status": "PASS"
    },
    {
      "model": "LINEAR",
      "attributed_revenue": 1250000.00,
      "roi_percent": 40.1,
      "reconciliation_status": "PASS"
    }
  ]
}
```

Values above are illustrative only. Attribution model revenue totals
should reconcile to the same eligible order-revenue universe when each
model fully allocates credit. Campaign-level distribution and ROI may
differ by model.

------------------------------------------------------------------------

## 12. Frontend Pages

### Page 1: Overview

-   KPI cards: campaigns, contacts, touchpoints, opportunities, eligible
    orders, spend, revenue and exception count.
-   Reporting currency and selected date range.
-   Run/validation status and data freshness.
-   Clear warnings for incomplete costs or unresolved currency.

### Page 2: Attribution Comparison

-   Select reporting period and attribution model.
-   Compare campaign attributed revenue and ROI by model.
-   Bar charts/table for campaign ranking.
-   Display unattributed revenue and reconciliation status.
-   Clearly label revenue attribution as allocation, not proof of
    causation.

### Page 3: Customer Journey Explorer

-   Search by synthetic contact ID, lead ID, opportunity ID or order ID.
-   Timeline of touchpoints and sessions.
-   Lead, opportunity, order and lifecycle events.
-   Highlight touches excluded because they occurred after conversion or
    outside the lookback window.
-   Link every displayed decision to source record IDs.

### Page 4: Exceptions and Data Quality

-   Filter by issue type, severity, status, entity and run.
-   Show expected vs actual decision where evaluation data permits.
-   Display issue details, related record IDs and resolution state.
-   Avoid exposing ground-truth labels to operational detection users by
    default.

### Page 5: Runs and Reproducibility

-   Seed, config version/hash, generator version, dataset scale and run
    status.
-   Row counts by entity.
-   File checksums and validation summary.
-   Comparison of two runs with same configuration.
-   Export links.

The UI is a presentation layer. Correctness of generation, attribution,
exception detection and reconciliation must be testable without the
frontend.

------------------------------------------------------------------------

## 13. Validation Rules and Acceptance Criteria

### 13.1 Structural checks

-   Every table's primary key is unique.
-   Every non-null foreign key points to an existing parent.
-   Required fields are non-null.
-   Enum values are valid.
-   Bridge-table pairs do not duplicate effective assignments.
-   All IDs follow their documented patterns.
-   Required records have consistent `is_synthetic` flags.
-   All table row counts are included in the run report.

### 13.2 Temporal checks

-   Campaign `start_at <= end_at`.
-   Creative/audience effective intervals are valid.
-   Session `ended_at >= started_at` when present.
-   Lead creation is consistent with its source session under the
    documented rule.
-   Opportunity creation is not earlier than its lead unless explicitly
    allowed and explained.
-   A won/lost opportunity has a close timestamp.
-   Order and lifecycle event transitions are valid.
-   A touch after conversion is allowed to exist as a source event only
    in a deliberate case; it must not be attributed to that conversion.

### 13.3 Financial checks

-   Amounts are non-negative unless a signed adjustment/refund model
    explicitly permits negatives.
-   Refund amount does not exceed gross amount under the chosen order
    model.
-   Source currency is retained.
-   Currency conversion requires a valid positive rate and rate date.
-   Attribution shares are in \[0, 1\].
-   Shares reconcile per fully attributed order.
-   Attributed revenue reconciles to eligible order revenue.
-   Duplicate economic transactions are counted once.
-   Missing cost coverage is not silently converted to zero.
-   ROI is unavailable for incomplete costs or zero cost.

### 13.4 Lifecycle and history checks

-   Allowed state transitions are documented.
-   Each transition has an event record.
-   Historical event rows are append-only.
-   Current status matches the latest valid event.
-   Corrections are recorded as new events or correction records.

### 13.5 Acceptance criteria

The build is accepted when: 1. Full-mode target counts are met: 500
campaigns, 50,000 contacts, 200,000 touchpoints and 10,000
opportunities. 2. All records have deterministic IDs and valid joins,
except deliberate and labelled anomaly cases. 3. All 12 core entities
have a field-level data dictionary. 4. First-touch, last-touch and
linear attribution are implemented and tested. 5. Temporal eligibility
and conversion windows are enforced. 6. All five required anomaly
scenarios are present in the labelled evaluation set and correctly
handled. 7. Financial totals and attribution allocations reconcile under
the documented policies. 8. Anonymous/unresolved identity links remain
visible and are not silently accepted. 9. State-change history is
preserved. 10. CSV, JSON and SQL seed outputs are produced with README,
schema, source manifest and validation summary. 11. Ground truth is
separate from detector inputs. 12. Two runs with identical seed/config
produce matching normalized row counts and checksums. 13. Chronological
evaluation periods are documented and applied. 14. The pipeline can be
run from a clean environment using documented commands.

------------------------------------------------------------------------

## 14. Reproducibility and Export Requirements

### 14.1 Files to produce

Recommended generated output:

``` text
data/generated/run_<run_id>/
├── campaign.csv
├── channel.csv
├── creative.csv
├── audience.csv
├── contact.csv
├── campaign_creative.csv
├── campaign_audience.csv
├── touchpoint.csv
├── web_session.csv
├── lead.csv
├── opportunity.csv
├── opportunity_event.csv
├── order.csv
├── order_event.csv
├── cost_record.csv
├── attribution_result.csv
├── attribution_touchpoint.csv
├── data_issue.csv
├── validation_result.csv
├── seed.sql
├── manifest.json
├── row_counts.json
├── checksums.sha256
└── validation_summary.json

data/ground_truth/
└── ground_truth.csv
```

If the ground truth file contains references to run-specific IDs, make
its run association explicit. Keep it outside the input directory used
by the detector.

### 14.2 Manifest contents

Include: - `run_id` - generation timestamp - generator version or Git
commit - seed - configuration file/hash - dataset scale - reporting
currency - time range - schema version - row counts - output file names
and SHA-256 checksums - anomaly injection settings - validation status -
public data source details, if any

Exclude secrets and personal data from the manifest.

### 14.3 Reproducibility procedure

1.  Run the generator with the same version, seed and configuration into
    run A.
2.  Run it again into run B.
3.  Normalize outputs by stable sorting on primary key and stable
    serialization.
4.  Exclude volatile operational fields such as generation timestamp or
    random run UUID from data-file checksum inputs, or keep them in a
    separate run manifest.
5.  Compare row counts per entity.
6.  Compare SHA-256 checksums for normalized entity files.
7.  Compare ground-truth case counts and labels.
8.  Fail the reproducibility check if any expected normalized output
    differs.
9.  Document any deliberate nondeterministic fields and ensure they do
    not affect analytical output.

A fixed seed alone does not guarantee reproducibility if generation
order, library versions, parallel execution or serialization order
changes. Record relevant versions and keep stable sorting.

------------------------------------------------------------------------

## 15. Testing Strategy

### 15.1 Unit tests

-   ID formatting and counters.
-   Seeded random generation.
-   Each attribution model.
-   Conversion-window boundaries.
-   Tie-breaking for identical timestamps.
-   Currency conversion and rounding.
-   ROI edge cases: missing cost, zero cost, negative/invalid amounts.
-   Duplicate economic transaction handling.
-   Unsupported identity handling.
-   Lifecycle transition rules.

### 15.2 Integration tests

-   Load generated files into a fresh PostgreSQL database.
-   Verify foreign keys and bridge relationships.
-   Reconstruct journeys with SQL/Python.
-   Run attribution and check revenue reconciliation.
-   Run exception detection on injected cases.
-   Export and reload CSV/JSON/SQL data.
-   Confirm event history is retained after state changes.

### 15.3 Acceptance tests

-   Required full-mode row counts.
-   Each of the five anomaly types is detected and handled as expected.
-   Ground truth is not accessible to the detector's input pipeline.
-   Attribution shares and revenue reconcile.
-   Missing identity links are visible.
-   Chronological periods are non-overlapping.
-   Two same-seed runs have matching normalized checksums.

### 15.4 Performance checks

-   Generate full target volumes within a documented runtime and memory
    envelope.
-   Use bulk database inserts rather than one insert per row where
    practical.
-   Add indexes for joins and filters.
-   Use pagination for UI queries.
-   Measure pipeline runtime by stage.
-   Avoid loading all large tables into memory unnecessarily; if needed,
    process in batches.
-   Record runtime and peak memory in the validation/run report.

------------------------------------------------------------------------

## 16. Implementation Milestones

  -----------------------------------------------------------------------
  Milestone               Work                    Exit criteria
  ----------------------- ----------------------- -----------------------
  M1 --- Requirements and Finalize definitions,   Reviewed schema and
  schema                  field dictionary,       rule documents
                          relationships, enums    
                          and attribution         
                          policies                

  M2 --- Starter          Build master and child  Repeatable starter data
  generator               generation for small    and valid IDs
                          scale                   

  M3 --- Database and     Create schema, load     Structural checks pass
  validation              data, enforce           on clean baseline
                          relationships and       
                          checks                  

  M4 --- Journey pipeline Join touches, sessions, Traceable journeys and
                          leads, opportunities    temporal checks
                          and orders              

  M5 --- Attribution      Implement first-touch,  Unit tests and share
  engine                  last-touch and linear   reconciliation pass
                          models                  

  M6 --- Finance and      Costs, currency policy, Expected decisions and
  exceptions              ROI, all five anomaly   financial
                          fixtures                reconciliation pass

  M7 --- Exports and      CSV/JSON/SQL, manifest, Two same-config runs
  reproducibility         ground truth, checksum  match
                          test                    

  M8 --- API and          Add endpoints and five  Analyst can compare
  dashboard               recommended UI pages    models and inspect
                                                  exceptions

  M9 --- Final            Run full data, test,    All acceptance criteria
  verification            document and package    satisfied
  -----------------------------------------------------------------------

Build M1--M7 before spending significant time on UI styling. If schedule
is limited, a command-line pipeline plus SQL reports can prove the core
business requirements before the dashboard is completed.

------------------------------------------------------------------------

## 17. Command-Line Interface

Provide stable commands in the README. Suggested interface:

``` bash
# Install project dependencies
python -m pip install -e .

# Generate starter dataset
python scripts/generate_data.py --config config/starter.yaml --output data/generated/starter

# Generate full dataset
python scripts/generate_data.py --config config/full.yaml --output data/generated/full

# Load data into a configured PostgreSQL database
python scripts/load_data.py --input data/generated/full

# Run structural and business validations
python scripts/validate_data.py --input data/generated/full

# Run journey reconstruction, attribution, ROI and exception analysis
python scripts/run_pipeline.py --input data/generated/full

# Export reports
python scripts/export_reports.py --run-id <run_id>

# Verify same-seed reproducibility
python scripts/verify_reproducibility.py --config config/starter.yaml
```

These are proposed command names; implement the commands and arguments
consistently. Document database setup, environment variables, expected
output directories and failure behavior. Do not commit real credentials.

------------------------------------------------------------------------

## 18. Risks and Decisions to Resolve Early

  -------------------------------------------------------------------------
  Risk / ambiguity        Decision needed         Recommended v1 choice
  ----------------------- ----------------------- -------------------------
  "Multi-touch" can mean  Select one definition   Linear credit by distinct
  equal per touch or                              eligible campaign;
  equal per campaign                              optionally add per-touch
                                                  as another model

  Campaign can have       Decide whether channel  One primary channel
  multiple channels       is single or            initially; add
                          many-to-many            campaign-channel bridge
                                                  if required

  What counts as a        Select timestamp and    Paid order timestamp for
  conversion              event                   revenue attribution

  Duplicate revenue       Decide economic         Deduplicate by stable
  definition              transaction key         economic transaction key;
                                                  preserve duplicate source
                                                  rows as issues

  Cost completeness       Determine expected      Track completeness
                          spend coverage          status; missing costs
                                                  make ROI
                                                  unavailable/provisional

  Currency source         Decide FX policy        Preserve source amount;
                                                  use dated, documented
                                                  rate or mark unresolved

  Anonymous session       Define acceptable       No identity assignment
  identity                evidence                without explicit evidence

  Long journeys across    Define period           Date-based conversion
  evaluation split        assignment              period plus documented
                                                  maturity/censoring policy

  Order-to-opportunity    Decide whether every    Optional FK, with
  relation                order requires an       explicit order-origin
                          opportunity             policy

  State changes           Decide history          Append-only
                          requirements            opportunity/order events
                                                  plus current status

  Scale/performance       Decide batch size and   Configurable batch
                          database load strategy  inserts and measured
                                                  stage timings

  Synthetic realism       Avoid unsupported       Document generated
                          claims                  distributions; cite
                                                  external sources only if
                                                  legally usable
  -------------------------------------------------------------------------

------------------------------------------------------------------------

## 19. Lawful Data Provenance

External data is optional. The recommended initial implementation uses
synthetic data only.

If public reference data is later used, maintain a source manifest
containing: - Source URL. - Dataset name and version. - Retrieval
date. - License and redistribution terms. - Attribution requirements. -
Fields retained and fields discarded. - Transformations applied. -
Reason the data is suitable for the intended use.

Do not bypass access controls or use confidential/personal data. If
licensing or suitability is uncertain, use synthetic data and use public
documentation only to inform schema design.

------------------------------------------------------------------------

## 20. Final Definition of Done

The project is complete when a reviewer can:

1.  Read the README and reproduce the environment.
2.  Generate starter and full synthetic datasets using the same
    codebase.
3.  Verify all required volume targets and deterministic IDs.
4.  Inspect the data dictionary and relational schema.
5.  Follow a contact's journey from touchpoints through session, lead,
    opportunity and order.
6.  Compare first-touch, last-touch and linear attribution.
7.  See how campaign cost, currency normalization and revenue affect
    ROI.
8.  Inspect all five deliberate anomaly scenarios and their recorded
    decisions.
9.  Verify ground truth is separate from detection inputs.
10. Run automated structural, temporal, lifecycle and financial
    validations.
11. Review event history without losing prior states.
12. Export CSV, JSON and SQL seed data with README, manifest and
    validation report.
13. Regenerate with the same seed/config and obtain matching normalized
    checksums.
14. Review measurable evaluation metrics and documented limitations.

**Priority rule:** Correctness, traceability, reconciliation and
reproducibility come before dashboard polish. A polished UI cannot
compensate for invalid joins, double-counted revenue, incorrect
attribution or missing evidence for identity links.
