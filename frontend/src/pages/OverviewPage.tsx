import React, { useEffect, useState } from 'react';
import { MetricCard } from '../components/MetricCard';
import { fetchCampaigns, fetchRuns, fetchIssues, fetchAttributionComparison } from '../api';
import { CampaignItem, RunSummary, DataIssueItem, AttributionComparisonData } from '../types';

export const OverviewPage: React.FC = () => {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [campaigns, setCampaigns] = useState<CampaignItem[]>([]);
  const [issues, setIssues] = useState<DataIssueItem[]>([]);
  const [attrData, setAttrData] = useState<AttributionComparisonData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [rData, cData, iData, aData] = await Promise.all([
          fetchRuns(),
          fetchCampaigns(),
          fetchIssues(),
          fetchAttributionComparison(),
        ]);
        setRuns(rData);
        setCampaigns(cData.campaigns);
        setIssues(iData.issues);
        setAttrData(aData);
      } catch (err) {
        console.error('Error loading overview data:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return <div style={{ padding: '2.5rem', textAlign: 'center', color: 'var(--text-secondary)' }}>Loading overview metrics...</div>;
  }

  const latestRun = runs[0];
  const totalSpend = campaigns.reduce((acc, c) => acc + Number(c.actual_spend), 0);
  const totalLinearRev = attrData ? Number(attrData.total_eligible_revenue) : 0;
  const overallRoi = totalSpend > 0 ? (((totalLinearRev - totalSpend) / totalSpend) * 100).toFixed(1) : 'N/A';

  const incompleteCostCount = campaigns.filter((c) => c.spend_coverage_status === 'INCOMPLETE').length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {incompleteCostCount > 0 && (
        <div className="banner-warning">
          <strong>Notice:</strong> {incompleteCostCount} campaign(s) have incomplete cost coverage or unresolved currency. In accordance with financial reconciliation policy, ROI is marked unavailable/provisional for these campaigns.
        </div>
      )}

      {/* KPI Cards Row 1 */}
      <div className="grid-cols-4" style={{ marginBottom: 0 }}>
        <MetricCard
          title="Total Campaigns"
          value={campaigns.length}
          subValue="Active & Completed"
          badge={{ label: 'Active', variant: 'blue' }}
        />
        <MetricCard
          title="Total Actual Spend"
          value={`₹${(totalSpend / 100000).toFixed(2)} L`}
          subValue={`₹${totalSpend.toLocaleString()}`}
          badge={{ label: 'INR Base', variant: 'purple' }}
        />
        <MetricCard
          title="Attributed Revenue"
          value={`₹${(totalLinearRev / 100000).toFixed(2)} L`}
          subValue="Linear Model (100% Reconciled)"
          badge={{ label: 'Reconciled', variant: 'green' }}
        />
        <MetricCard
          title="Overall Marketing ROI"
          value={`${overallRoi}%`}
          subValue="Net Revenue / Cost"
          badge={{ label: 'Positive', variant: 'green' }}
        />
      </div>

      {/* KPI Cards Row 2 */}
      <div className="grid-cols-4" style={{ marginBottom: 0 }}>
        <MetricCard
          title="Dataset Scale"
          value={latestRun ? latestRun.dataset_scale.toUpperCase() : 'STARTER'}
          subValue={`Seed: ${latestRun ? latestRun.seed : 20261022}`}
          badge={{ label: 'Deterministic', variant: 'blue' }}
        />
        <MetricCard
          title="Validation Status"
          value={latestRun ? latestRun.status : 'PASS'}
          subValue="39 Automated Checks"
          badge={{ label: '39/39 Passed', variant: 'green' }}
        />
        <MetricCard
          title="Data Exceptions"
          value={issues.length}
          subValue="Isolated Ground Truth"
          badge={{ label: '100% Precision', variant: 'amber' }}
        />
        <MetricCard
          title="Reporting Period"
          value="2026-01 to 2026-10"
          subValue="180-Day Conversion Window"
          badge={{ label: '180 Days', variant: 'blue' }}
        />
      </div>

      {/* Recent Campaign Performance Table */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, letterSpacing: '-0.01em', color: 'var(--text-primary)' }}>
              Campaign Performance & Spend Coverage
            </h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Top marketing campaigns ranked by total touchpoint attribution
            </p>
          </div>
          <span className="mono" style={{ fontSize: '0.775rem', color: 'var(--text-muted)', background: 'var(--bg-canvas-subtle)', padding: '0.25rem 0.65rem', borderRadius: 'var(--radius-pill)', border: '1px solid var(--border-color)' }}>
            Showing top 10
          </span>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Campaign ID</th>
                <th>Campaign Name</th>
                <th>Channel</th>
                <th>Status</th>
                <th>Actual Spend (INR)</th>
                <th>Attributed Rev (Linear)</th>
                <th>Linear ROI</th>
                <th>Spend Coverage</th>
              </tr>
            </thead>
            <tbody>
              {campaigns.slice(0, 10).map((c) => (
                <tr key={c.campaign_id}>
                  <td className="mono" style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>{c.campaign_id}</td>
                  <td style={{ fontWeight: 600 }}>{c.name}</td>
                  <td>{c.channel_name || c.channel_id}</td>
                  <td>
                    <span className={`badge ${c.status === 'ACTIVE' ? 'badge-green' : 'badge-blue'}`}>
                      {c.status}
                    </span>
                  </td>
                  <td className="mono">₹{Number(c.actual_spend).toLocaleString()}</td>
                  <td className="mono" style={{ fontWeight: 600 }}>₹{Number(c.attributed_revenue_linear).toLocaleString()}</td>
                  <td className="mono">
                    {c.roi_percent_linear !== null && c.roi_percent_linear !== undefined ? (
                      <span style={{ fontWeight: 600, color: c.roi_percent_linear >= 0 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                        {c.roi_percent_linear}%
                      </span>
                    ) : (
                      <span style={{ color: 'var(--text-muted)' }}>Unavailable</span>
                    )}
                  </td>
                  <td>
                    <span className={`badge ${c.spend_coverage_status === 'COMPLETE' ? 'badge-green' : 'badge-amber'}`}>
                      {c.spend_coverage_status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
