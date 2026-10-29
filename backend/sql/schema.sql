-- ============================================================================
-- Marketing Campaign Attribution & ROI Analysis System - Relational DDL
-- Target Engine: PostgreSQL 14+ (Compatible with SQLAlchemy & Seed Generators)
-- ============================================================================

-- 1. Master Channel Table
CREATE TABLE IF NOT EXISTS channel (
    channel_id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(80) NOT NULL UNIQUE,
    channel_type VARCHAR(30) NOT NULL CHECK (channel_type IN (
        'PAID_SEARCH', 'PAID_SOCIAL', 'EMAIL', 'ORGANIC', 'REFERRAL', 'OFFLINE', 'DISPLAY', 'OTHER'
    )),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL
);

-- 2. Master Campaign Table
CREATE TABLE IF NOT EXISTS campaign (
    campaign_id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(160) NOT NULL,
    channel_id VARCHAR(32) NOT NULL REFERENCES channel(channel_id),
    budget_amount NUMERIC(18,2) NOT NULL CHECK (budget_amount >= 0),
    currency CHAR(3) NOT NULL,
    start_at TIMESTAMPTZ NOT NULL,
    end_at TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('DRAFT', 'PLANNED', 'ACTIVE', 'PAUSED', 'COMPLETED', 'CANCELLED')),
    objective VARCHAR(80),
    created_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT chk_campaign_dates CHECK (start_at <= end_at)
);
CREATE INDEX IF NOT EXISTS idx_campaign_channel ON campaign(channel_id);
CREATE INDEX IF NOT EXISTS idx_campaign_dates ON campaign(start_at, end_at);

-- 3. Master Creative Table
CREATE TABLE IF NOT EXISTS creative (
    creative_id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    format VARCHAR(30) NOT NULL CHECK (format IN ('TEXT', 'IMAGE', 'VIDEO', 'LANDING_PAGE', 'BANNER', 'OTHER')),
    version VARCHAR(30) NOT NULL,
    active_from TIMESTAMPTZ NOT NULL,
    active_to TIMESTAMPTZ,
    metadata_json JSONB,
    CONSTRAINT chk_creative_dates CHECK (active_to IS NULL OR active_to >= active_from)
);

-- 4. Master Audience Table
CREATE TABLE IF NOT EXISTS audience (
    audience_id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    segment_type VARCHAR(40) NOT NULL CHECK (segment_type IN ('NEW', 'RETURNING', 'HIGH_INTENT', 'GENERAL', 'BUSINESS', 'OTHER')),
    criteria_json JSONB,
    effective_from TIMESTAMPTZ NOT NULL,
    effective_to TIMESTAMPTZ,
    CONSTRAINT chk_audience_dates CHECK (effective_to IS NULL OR effective_to >= effective_from)
);

-- 5. Master Contact Table
CREATE TABLE IF NOT EXISTS contact (
    contact_id VARCHAR(32) PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL,
    region VARCHAR(40),
    customer_segment VARCHAR(40),
    consent_status VARCHAR(20) NOT NULL CHECK (consent_status IN ('UNKNOWN', 'GRANTED', 'DENIED', 'WITHDRAWN')),
    is_synthetic BOOLEAN NOT NULL DEFAULT TRUE CHECK (is_synthetic = TRUE),
    identity_status VARCHAR(20) NOT NULL CHECK (identity_status IN ('KNOWN', 'PARTIAL', 'UNRESOLVED'))
);
CREATE INDEX IF NOT EXISTS idx_contact_created ON contact(created_at);

-- 6. Campaign-Creative Bridge
CREATE TABLE IF NOT EXISTS campaign_creative (
    campaign_id VARCHAR(32) NOT NULL REFERENCES campaign(campaign_id),
    creative_id VARCHAR(32) NOT NULL REFERENCES creative(creative_id),
    effective_from TIMESTAMPTZ NOT NULL,
    effective_to TIMESTAMPTZ,
    PRIMARY KEY (campaign_id, creative_id, effective_from),
    CONSTRAINT chk_cmp_creative_dates CHECK (effective_to IS NULL OR effective_to >= effective_from)
);

-- 7. Campaign-Audience Bridge
CREATE TABLE IF NOT EXISTS campaign_audience (
    campaign_id VARCHAR(32) NOT NULL REFERENCES campaign(campaign_id),
    audience_id VARCHAR(32) NOT NULL REFERENCES audience(audience_id),
    effective_from TIMESTAMPTZ NOT NULL,
    effective_to TIMESTAMPTZ,
    PRIMARY KEY (campaign_id, audience_id, effective_from),
    CONSTRAINT chk_cmp_audience_dates CHECK (effective_to IS NULL OR effective_to >= effective_from)
);

-- 8. Touchpoint Table
CREATE TABLE IF NOT EXISTS touchpoint (
    touchpoint_id VARCHAR(80) PRIMARY KEY,
    contact_id VARCHAR(32) REFERENCES contact(contact_id),
    campaign_id VARCHAR(32) REFERENCES campaign(campaign_id),
    channel_id VARCHAR(32) NOT NULL REFERENCES channel(channel_id),
    creative_id VARCHAR(32) REFERENCES creative(creative_id),
    occurred_at TIMESTAMPTZ NOT NULL,
    touch_type VARCHAR(30) NOT NULL CHECK (touch_type IN (
        'IMPRESSION', 'CLICK', 'EMAIL_OPEN', 'EMAIL_CLICK', 'FORM_SUBMIT',
        'PHONE_CALL', 'EVENT_ATTENDANCE', 'SALES_TOUCH', 'OTHER'
    )),
    touch_mode VARCHAR(12) NOT NULL CHECK (touch_mode IN ('ONLINE', 'OFFLINE')),
    source_event_id VARCHAR(80),
    identity_evidence VARCHAR(30) NOT NULL CHECK (identity_evidence IN (
        'AUTHENTICATED', 'CONSENTED_MATCH', 'SESSION_LINK', 'NONE', 'UNKNOWN'
    )),
    issue_type VARCHAR(50),
    is_synthetic BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE INDEX IF NOT EXISTS idx_touchpoint_contact ON touchpoint(contact_id);
CREATE INDEX IF NOT EXISTS idx_touchpoint_campaign ON touchpoint(campaign_id);
CREATE INDEX IF NOT EXISTS idx_touchpoint_occurred ON touchpoint(occurred_at);

-- 9. Web Session Table
CREATE TABLE IF NOT EXISTS web_session (
    session_id VARCHAR(32) PRIMARY KEY,
    contact_id VARCHAR(32) REFERENCES contact(contact_id),
    campaign_id VARCHAR(32) REFERENCES campaign(campaign_id),
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    source_channel_id VARCHAR(32) REFERENCES channel(channel_id),
    landing_path VARCHAR(200),
    identity_evidence VARCHAR(30) NOT NULL CHECK (identity_evidence IN (
        'AUTHENTICATED', 'CONSENTED_MATCH', 'SESSION_LINK', 'NONE', 'UNKNOWN'
    )),
    is_anonymous BOOLEAN NOT NULL DEFAULT FALSE,
    issue_type VARCHAR(50),
    CONSTRAINT chk_session_dates CHECK (ended_at IS NULL OR ended_at >= started_at)
);
CREATE INDEX IF NOT EXISTS idx_session_contact ON web_session(contact_id);
CREATE INDEX IF NOT EXISTS idx_session_campaign ON web_session(campaign_id);
CREATE INDEX IF NOT EXISTS idx_session_started ON web_session(started_at);

-- 10. Lead Table
CREATE TABLE IF NOT EXISTS lead (
    lead_id VARCHAR(32) PRIMARY KEY,
    contact_id VARCHAR(32) NOT NULL REFERENCES contact(contact_id),
    session_id VARCHAR(32) REFERENCES web_session(session_id),
    created_at TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('NEW', 'QUALIFIED', 'DISQUALIFIED', 'CONVERTED', 'CLOSED')),
    source_type VARCHAR(20) NOT NULL CHECK (source_type IN ('WEB', 'OFFLINE', 'REFERRAL', 'SALES', 'OTHER')),
    qualification_at TIMESTAMPTZ,
    issue_type VARCHAR(50),
    CONSTRAINT chk_lead_qual_dates CHECK (qualification_at IS NULL OR qualification_at >= created_at)
);
CREATE INDEX IF NOT EXISTS idx_lead_contact ON lead(contact_id);
CREATE INDEX IF NOT EXISTS idx_lead_session ON lead(session_id);

-- 11. Opportunity Table
CREATE TABLE IF NOT EXISTS opportunity (
    opportunity_id VARCHAR(32) PRIMARY KEY,
    lead_id VARCHAR(32) NOT NULL REFERENCES lead(lead_id),
    created_at TIMESTAMPTZ NOT NULL,
    expected_value NUMERIC(18,2) NOT NULL CHECK (expected_value >= 0),
    currency CHAR(3) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('OPEN', 'QUALIFIED', 'PROPOSAL', 'WON', 'LOST', 'CANCELLED')),
    closed_at TIMESTAMPTZ,
    actual_closed_value NUMERIC(18,2),
    issue_type VARCHAR(50),
    CONSTRAINT chk_opp_closed_dates CHECK (closed_at IS NULL OR closed_at >= created_at)
);
CREATE INDEX IF NOT EXISTS idx_opp_lead ON opportunity(lead_id);
CREATE INDEX IF NOT EXISTS idx_opp_status ON opportunity(status);

-- 12. Order Table
CREATE TABLE IF NOT EXISTS "order" (
    order_id VARCHAR(32) PRIMARY KEY,
    opportunity_id VARCHAR(32) REFERENCES opportunity(opportunity_id),
    contact_id VARCHAR(32) NOT NULL REFERENCES contact(contact_id),
    ordered_at TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('PENDING', 'PAID', 'REFUNDED', 'PARTIALLY_REFUNDED', 'CANCELLED')),
    gross_amount NUMERIC(18,2) NOT NULL CHECK (gross_amount >= 0),
    refund_amount NUMERIC(18,2) NOT NULL CHECK (refund_amount >= 0 AND refund_amount <= gross_amount),
    net_revenue NUMERIC(18,2) NOT NULL CHECK (net_revenue >= 0),
    currency CHAR(3) NOT NULL,
    economic_transaction_key VARCHAR(80) NOT NULL,
    issue_type VARCHAR(50)
);
CREATE INDEX IF NOT EXISTS idx_order_contact ON "order"(contact_id);
CREATE INDEX IF NOT EXISTS idx_order_opportunity ON "order"(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_order_ordered_at ON "order"(ordered_at);
CREATE INDEX IF NOT EXISTS idx_order_economic_key ON "order"(economic_transaction_key);

-- 13. Campaign Cost Record Table
CREATE TABLE IF NOT EXISTS cost_record (
    cost_record_id VARCHAR(32) PRIMARY KEY,
    campaign_id VARCHAR(32) NOT NULL REFERENCES campaign(campaign_id),
    incurred_at TIMESTAMPTZ NOT NULL,
    cost_type VARCHAR(30) NOT NULL CHECK (cost_type IN ('MEDIA', 'AGENCY', 'PRODUCTION', 'PLATFORM', 'OTHER')),
    amount NUMERIC(18,2) NOT NULL CHECK (amount >= 0),
    currency CHAR(3) NOT NULL,
    exchange_rate_to_reporting NUMERIC(18,8),
    reporting_amount NUMERIC(18,2),
    rate_date DATE,
    source_reference VARCHAR(80),
    issue_type VARCHAR(50)
);
CREATE INDEX IF NOT EXISTS idx_cost_campaign ON cost_record(campaign_id);
CREATE INDEX IF NOT EXISTS idx_cost_incurred ON cost_record(incurred_at);

-- 14. Attribution Result Table
CREATE TABLE IF NOT EXISTS attribution_result (
    attribution_result_id VARCHAR(80) PRIMARY KEY,
    order_id VARCHAR(32) NOT NULL REFERENCES "order"(order_id),
    campaign_id VARCHAR(32) REFERENCES campaign(campaign_id),
    model_name VARCHAR(30) NOT NULL CHECK (model_name IN ('FIRST_TOUCH', 'LAST_TOUCH', 'LINEAR')),
    model_version VARCHAR(20) NOT NULL,
    credit_share NUMERIC(9,6) NOT NULL CHECK (credit_share >= 0 AND credit_share <= 1),
    attributed_revenue NUMERIC(18,2) NOT NULL CHECK (attributed_revenue >= 0),
    calculated_at TIMESTAMPTZ NOT NULL,
    decision_reason VARCHAR(200),
    run_id VARCHAR(40) NOT NULL,
    issue_type VARCHAR(50)
);
CREATE INDEX IF NOT EXISTS idx_attr_order ON attribution_result(order_id);
CREATE INDEX IF NOT EXISTS idx_attr_campaign ON attribution_result(campaign_id);
CREATE INDEX IF NOT EXISTS idx_attr_model ON attribution_result(model_name, model_version);

-- 15. Attribution Touchpoint Bridge Table
CREATE TABLE IF NOT EXISTS attribution_touchpoint (
    attribution_result_id VARCHAR(80) NOT NULL REFERENCES attribution_result(attribution_result_id),
    touchpoint_id VARCHAR(80) NOT NULL REFERENCES touchpoint(touchpoint_id),
    contribution_weight NUMERIC(9,6) NOT NULL CHECK (contribution_weight >= 0),
    PRIMARY KEY (attribution_result_id, touchpoint_id)
);

-- 16. Opportunity Event History Table (Append-Only)
CREATE TABLE IF NOT EXISTS opportunity_event (
    opportunity_event_id VARCHAR(32) PRIMARY KEY,
    opportunity_id VARCHAR(32) NOT NULL REFERENCES opportunity(opportunity_id),
    event_type VARCHAR(40) NOT NULL,
    old_status VARCHAR(20),
    new_status VARCHAR(20),
    occurred_at TIMESTAMPTZ NOT NULL,
    event_payload JSONB,
    run_id VARCHAR(40)
);
CREATE INDEX IF NOT EXISTS idx_opp_event_opp ON opportunity_event(opportunity_id);

-- 17. Order Event History Table (Append-Only)
CREATE TABLE IF NOT EXISTS order_event (
    order_event_id VARCHAR(32) PRIMARY KEY,
    order_id VARCHAR(32) NOT NULL REFERENCES "order"(order_id),
    event_type VARCHAR(40) NOT NULL CHECK (event_type IN ('CREATED', 'PAID', 'REFUNDED', 'CANCELLED', 'CORRECTED')),
    old_status VARCHAR(20),
    new_status VARCHAR(20),
    occurred_at TIMESTAMPTZ NOT NULL,
    event_payload JSONB,
    run_id VARCHAR(40)
);
CREATE INDEX IF NOT EXISTS idx_order_event_order ON order_event(order_id);

-- 18. Pipeline Run Execution Table
CREATE TABLE IF NOT EXISTS pipeline_run (
    run_id VARCHAR(40) PRIMARY KEY,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    seed BIGINT NOT NULL,
    generator_version VARCHAR(20) NOT NULL,
    config_hash VARCHAR(64) NOT NULL,
    dataset_scale VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED')),
    row_counts_json JSONB,
    checksums_json JSONB
);

-- 19. Data Issue Finding Table
CREATE TABLE IF NOT EXISTS data_issue (
    issue_id VARCHAR(32) PRIMARY KEY,
    run_id VARCHAR(40) REFERENCES pipeline_run(run_id),
    entity_type VARCHAR(40) NOT NULL,
    entity_id VARCHAR(80) NOT NULL,
    issue_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('INFO', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    detected_at TIMESTAMPTZ NOT NULL,
    decision VARCHAR(80),
    resolution_status VARCHAR(20) NOT NULL CHECK (resolution_status IN ('OPEN', 'ACKNOWLEDGED', 'RESOLVED', 'ACCEPTED')),
    details_json JSONB
);
CREATE INDEX IF NOT EXISTS idx_issue_entity ON data_issue(entity_type, entity_id);

-- 20. Validation Result Table
CREATE TABLE IF NOT EXISTS validation_result (
    validation_result_id VARCHAR(32) PRIMARY KEY,
    run_id VARCHAR(40) REFERENCES pipeline_run(run_id),
    check_name VARCHAR(100) NOT NULL,
    entity_name VARCHAR(40) NOT NULL,
    records_checked INTEGER NOT NULL,
    failure_count INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('PASS', 'FAIL', 'WARNING')),
    details_json JSONB,
    executed_at TIMESTAMPTZ NOT NULL
);

