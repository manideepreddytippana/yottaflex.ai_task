# Attribution Rules Specification

Version: 1.0  
Status: Approved

---

## 1. Touchpoint Eligibility Rules

A touchpoint $T$ is eligible for attributing conversion order $O$ if and only if all of the following conditions are met:

1. **Temporal Precedence:** $T.\text{occurred\_at} \le O.\text{ordered\_at}$.  
   Post-conversion touchpoints are strictly ineligible for that conversion.
2. **Lookback Window:** $T.\text{occurred\_at} \ge (O.\text{ordered\_at} - \Delta t_{\text{lookback}})$, where $\Delta t_{\text{lookback}} = 180 \text{ days}$ by default.
3. **Campaign Association:** $T.\text{campaign\_id}$ is not null and refers to a valid campaign (or is assigned to an explicitly defined unattributed bucket).
4. **Identity Linkage:** $T$ belongs to the confirmed customer journey of $O.\text{contact\_id}$ backed by valid identity evidence (`AUTHENTICATED`, `CONSENTED_MATCH`, or verified `SESSION_LINK`).
5. **Deduplication:** Rapid repetitive pings within the same touch channel within a deduplication threshold are collapsed.
6. **Active Timeline:** The associated campaign was active or validly effective at touch time.

---

## 2. Model Specifications

### 2.1 First-Touch Model
- **Logic:** Sort all eligible touchpoints ascending by `occurred_at`. Deterministically tie-break on `touchpoint_id`.
- **Allocation:** 100% of order net revenue is assigned to the campaign of the earliest eligible touchpoint.
- If no eligible touchpoint exists, 100% is assigned to the `UNATTRIBUTED` bucket.

### 2.2 Last-Touch Model
- **Logic:** Sort all eligible touchpoints descending by `occurred_at`. Deterministically tie-break on `touchpoint_id`.
- **Allocation:** 100% of order net revenue is assigned to the campaign of the latest eligible touchpoint occurring on or before conversion.
- If no eligible touchpoint exists, 100% is assigned to the `UNATTRIBUTED` bucket.

### 2.3 Linear Multi-Touch Model
- **V1 Standard Policy:** Credit is split equally across **distinct eligible campaigns** participating in the journey:
  $$w_{\text{share}} = \frac{1}{n_{\text{campaigns}}}$$
- **Cent Allocation & Remainder Rule:**  
  Attributed revenue per campaign is calculated using decimal arithmetic (`NUMERIC(18,2)`):
  $$\text{base\_amount} = \lfloor \text{net\_revenue} \times w_{\text{share}} \rfloor$$
  Any fractional remainder (cents) is deterministically allocated to the earliest eligible campaign in chronological order:
  $$\sum \text{Attributed Revenue} \equiv \text{Order Net Revenue}$$

---

## 3. Financial Reconciliation Invariants
1. For every attributed order:
   $$\sum \text{credit\_share} = 1.000000 \pm 10^{-6}$$
2. For every attributed order:
   $$\sum \text{attributed\_revenue} = O.\text{net\_revenue}$$
3. Across all orders:
   $$\sum \text{Attributed Revenue} + \sum \text{Unattributed Revenue} = \sum \text{Eligible Net Revenue}$$

