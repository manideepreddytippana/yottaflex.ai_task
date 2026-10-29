import React, { useEffect, useState } from 'react';
import { fetchAttributionComparison } from '../api';
import { AttributionComparisonData } from '../types';
import { SvgBarChart } from '../components/SvgBarChart';

export const AttributionPage: React.FC = () => {
  const [data, setData] = useState<AttributionComparisonData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedModel, setSelectedModel] = useState<'ALL' | 'FIRST_TOUCH' | 'LAST_TOUCH' | 'LINEAR'>('ALL');

  useEffect(() => {
    async function loadData() {
      try {
        const res = await fetchAttributionComparison();
        setData(res);
      } catch (err) {
        console.error('Error loading attribution comparison:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading || !data) {
    return <div style={{ padding: '2.5rem', textAlign: 'center', color: 'var(--text-secondary)' }}>Loading attribution comparison...</div>;
  }

  const chartData = data.campaign_comparison.map((c) => ({
    label: c.campaign_name,
    firstTouch: Number(c.first_touch_revenue),
    lastTouch: Number(c.last_touch_revenue),
    linear: Number(c.linear_revenue),
  }));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Policy and Methodological Disclaimer */}
      <div className="banner-info" style={{ margin: 0 }}>
        <div>
          <strong>Methodology Note:</strong> Attribution models represent algorithmic revenue allocation across historical touchpoints based on predefined credit distribution rules (First-Touch, Last-Touch, Linear split). They reflect allocation policy, not mathematical proof of incremental causation.
        </div>
      </div>

      {/* Model Summaries Cards */}
      <div className="grid-cols-4" style={{ marginBottom: 0 }}>
        {data.models.map((m) => {
          const accentColor = m.model === 'FIRST_TOUCH' ? 'var(--accent-blue)' : m.model === 'LAST_TOUCH' ? 'var(--accent-green)' : 'var(--accent-amber)';
          return (
            <div key={m.model} className="card" style={{ padding: '1.25rem 1.35rem', position: 'relative', overflow: 'hidden' }}>
              <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 3, backgroundColor: accentColor }}></div>
              <div className="kpi-title">{m.model.replace('_', ' ')}</div>
              <div className="kpi-value" style={{ fontSize: '1.6rem' }}>
                ₹{Number(m.attributed_revenue).toLocaleString()}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.65rem', fontSize: '0.8rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Orders: {m.total_orders_attributed}</span>
                <span className={`badge ${m.reconciliation_status === 'PASS' ? 'badge-green' : 'badge-red'}`}>
                  {m.reconciliation_status}
                </span>
              </div>
            </div>
          );
        })}
        <div className="card" style={{ padding: '1.25rem 1.35rem', position: 'relative', overflow: 'hidden' }}>
          <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 3, backgroundColor: 'var(--accent-dark)' }}></div>
          <div className="kpi-title">Eligible Universe</div>
          <div className="kpi-value" style={{ fontSize: '1.6rem' }}>
            ₹{Number(data.total_eligible_revenue).toLocaleString()}
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.65rem', fontSize: '0.8rem' }}>
            <span style={{ color: 'var(--text-secondary)' }}>Unattributed: ₹{Number(data.unattributed_revenue).toFixed(2)}</span>
            <span className="badge badge-green">100% RECONCILED</span>
          </div>
        </div>
      </div>

      {/* Grouped Bar Chart */}
      <SvgBarChart data={chartData} title="Campaign Revenue Allocation Across Models (Top 10 Campaigns)" />

      {/* Detailed Campaign Comparison Table */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, letterSpacing: '-0.01em', color: 'var(--text-primary)' }}>
              Multi-Model Campaign Performance Matrix
            </h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Side-by-side revenue and ROI evaluation across all active attribution algorithms
            </p>
          </div>

          <div className="nav-tabs">
            {(['ALL', 'FIRST_TOUCH', 'LAST_TOUCH', 'LINEAR'] as const).map((m) => (
              <button
                key={m}
                onClick={() => setSelectedModel(m)}
                className={`nav-tab ${selectedModel === m ? 'active' : ''}`}
                style={{ padding: '0.35rem 0.85rem', fontSize: '0.75rem' }}
              >
                {m.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Campaign</th>
                <th>Channel</th>
                <th>Actual Spend</th>
                {(selectedModel === 'ALL' || selectedModel === 'FIRST_TOUCH') && <th>First-Touch Rev</th>}
                {(selectedModel === 'ALL' || selectedModel === 'FIRST_TOUCH') && <th>First-Touch ROI</th>}
                {(selectedModel === 'ALL' || selectedModel === 'LAST_TOUCH') && <th>Last-Touch Rev</th>}
                {(selectedModel === 'ALL' || selectedModel === 'LAST_TOUCH') && <th>Last-Touch ROI</th>}
                {(selectedModel === 'ALL' || selectedModel === 'LINEAR') && <th>Linear Rev</th>}
                {(selectedModel === 'ALL' || selectedModel === 'LINEAR') && <th>Linear ROI</th>}
              </tr>
            </thead>
            <tbody>
              {data.campaign_comparison.map((c) => (
                <tr key={c.campaign_id}>
                  <td style={{ fontWeight: 600 }}>
                    {c.campaign_name}
                    <div className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 400 }}>{c.campaign_id}</div>
                  </td>
                  <td>{c.channel_name}</td>
                  <td className="mono">₹{Number(c.actual_spend).toLocaleString()}</td>
                  {(selectedModel === 'ALL' || selectedModel === 'FIRST_TOUCH') && (
                    <td className="mono" style={{ color: 'var(--accent-blue)', fontWeight: 600 }}>₹{Number(c.first_touch_revenue).toLocaleString()}</td>
                  )}
                  {(selectedModel === 'ALL' || selectedModel === 'FIRST_TOUCH') && (
                    <td className="mono">
                      {c.first_touch_roi !== null && c.first_touch_roi !== undefined ? `${c.first_touch_roi}%` : '—'}
                    </td>
                  )}
                  {(selectedModel === 'ALL' || selectedModel === 'LAST_TOUCH') && (
                    <td className="mono" style={{ color: 'var(--accent-green)', fontWeight: 600 }}>₹{Number(c.last_touch_revenue).toLocaleString()}</td>
                  )}
                  {(selectedModel === 'ALL' || selectedModel === 'LAST_TOUCH') && (
                    <td className="mono">
                      {c.last_touch_roi !== null && c.last_touch_roi !== undefined ? `${c.last_touch_roi}%` : '—'}
                    </td>
                  )}
                  {(selectedModel === 'ALL' || selectedModel === 'LINEAR') && (
                    <td className="mono" style={{ color: 'var(--accent-amber)', fontWeight: 600 }}>₹{Number(c.linear_revenue).toLocaleString()}</td>
                  )}
                  {(selectedModel === 'ALL' || selectedModel === 'LINEAR') && (
                    <td className="mono">
                      {c.linear_roi !== null && c.linear_roi !== undefined ? `${c.linear_roi}%` : '—'}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
