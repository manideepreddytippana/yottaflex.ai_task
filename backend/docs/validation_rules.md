# Data Validation Rules and Quality Checks

---

## 1. Structural Checks
- **Primary Key Uniqueness:** Every table's primary key must be unique across all records.
- **Foreign Key Referential Integrity:** Every non-null foreign key must point to an existing parent entity.
- **Required Fields:** All NOT NULL columns must contain valid values.
- **Enum Validity:** Statuses, channel types, creative formats, touch types, and identity evidences must belong to the approved domain sets.
- **ID Format Integrity:** All identifiers must match their respective regex patterns without variation.

---

## 2. Temporal Checks
- **Campaign Active Dates:** $\text{start\_at} \le \text{end\_at}$.
- **Creative Effective Dates:** $\text{active\_to} \ge \text{active\_from}$ (when `active_to` is populated).
- **Session Duration:** $\text{ended\_at} \ge \text{started\_at}$ (when `ended_at` is populated).
- **Lead to Opportunity:** $\text{opportunity.created\_at} \ge \text{lead.created\_at}$.
- **Opportunity Lifecycle:** $\text{opportunity.closed\_at} \ge \text{opportunity.created\_at}$ for `WON` and `LOST` opportunities.
- **Touchpoint to Order:** Touchpoints occurring after `ordered_at` must never be eligible for attribution of that order.

---

## 3. Financial Checks
- **Non-Negative Values:** Budgets, expected values, actual costs, and gross amounts must be $\ge 0$.
- **Refund Arithmetic:** $0 \le \text{refund\_amount} \le \text{gross\_amount}$.
- **Net Revenue Derivation:** $\text{net\_revenue} \equiv \text{gross\_amount} - \text{refund\_amount}$.
- **Attribution Share Bound:** $0.0 \le \text{credit\_share} \le 1.0$.
- **Reconciliation Invariants:**
  - Share sum per order $= 1.0 \pm 10^{-6}$.
  - Attributed revenue sum per order $\equiv \text{net\_revenue}$.
- **ROI Computation Invariants:**
  - $\text{ROI} = \frac{\text{Attributed Revenue} - \text{Actual Cost}}{\text{Actual Cost}} \times 100\%$.
  - Undefined (`N/A`) when $\text{Actual Cost} = 0$.
  - Incomplete (`INCOMPLETE_COST`) when cost coverage is partial or exchange rates are missing.

---

## 4. Anomaly Detection Tests (5 Scenarios)
1. **Duplicate Revenue:** Flag duplicated `economic_transaction_key` values; attribute revenue once only.
2. **Post-Conversion Touches:** Flag touchpoints occurring after `ordered_at`; exclude from attribution eligibility.
3. **Currency Mismatch:** Flag cost records lacking a valid conversion exchange rate for the reporting currency.
4. **Missing Costs:** Flag active campaigns with missing cost records; prevent false high ROI.
5. **Unsupported Identity Links:** Flag anonymous sessions linked to contacts without valid evidence (`AUTHENTICATED`, `CONSENTED_MATCH`).

