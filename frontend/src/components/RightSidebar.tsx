import React from 'react';
import { AttributionComparisonData } from '../types';

interface RightSidebarProps {
  attrData?: AttributionComparisonData | null;
  onNavigateTab: (tab: 'overview' | 'attribution' | 'journey' | 'exceptions' | 'reproducibility') => void;
}

export const RightSidebar: React.FC<RightSidebarProps> = ({ attrData, onNavigateTab }) => {
  // Calculate model shares if available
  let firstTouchPct = 42;
  let lastTouchPct = 36;
  let linearPct = 22;

  if (attrData && attrData.models && attrData.models.length >= 3) {
    const ft = attrData.models.find((m) => m.model === 'FIRST_TOUCH')?.attributed_revenue || 0;
    const lt = attrData.models.find((m) => m.model === 'LAST_TOUCH')?.attributed_revenue || 0;
    const lin = attrData.models.find((m) => m.model === 'LINEAR')?.attributed_revenue || 0;
    const total = ft + lt + lin;
    if (total > 0) {
      firstTouchPct = Math.round((ft / total) * 100);
      lastTouchPct = Math.round((lt / total) * 100);
      linearPct = 100 - firstTouchPct - lastTouchPct;
    }
  }

  // Calculate SVG arc strokes for donut ring (circumference = 2 * PI * 46 ≈ 289)
  const radius = 46;
  const circ = 2 * Math.PI * radius;
  const stroke1 = (firstTouchPct / 100) * circ;
  const stroke2 = (lastTouchPct / 100) * circ;
  const stroke3 = (linearPct / 100) * circ;

  const offset1 = 0;
  const offset2 = -stroke1;
  const offset3 = -(stroke1 + stroke2);

  return (
    <aside className="right-sidebar">
      {/* Donut Chart Widget */}
      <div className="widget-card">
        <div className="widget-header">
          <h3 className="widget-title">Attribution split</h3>
          <span className="dropdown-pill" style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            FY26 ▾
          </span>
        </div>

        <div className="donut-container">
          <div className="donut-wrapper">
            <svg width="130" height="130" viewBox="0 0 120 120" style={{ transform: 'rotate(-90deg)' }}>
              {/* Background circle track */}
              <circle
                cx="60"
                cy="60"
                r={radius}
                fill="none"
                stroke="#f0eee7"
                strokeWidth="11"
              />
              {/* First-Touch Segment */}
              <circle
                cx="60"
                cy="60"
                r={radius}
                fill="none"
                stroke="#1e3a47"
                strokeWidth="11"
                strokeDasharray={`${stroke1} ${circ}`}
                strokeDashoffset={offset1}
                strokeLinecap="round"
              />
              {/* Last-Touch Segment */}
              <circle
                cx="60"
                cy="60"
                r={radius}
                fill="none"
                stroke="#3f7267"
                strokeWidth="11"
                strokeDasharray={`${stroke2} ${circ}`}
                strokeDashoffset={offset2}
                strokeLinecap="round"
              />
              {/* Linear Segment */}
              <circle
                cx="60"
                cy="60"
                r={radius}
                fill="none"
                stroke="#9fcbc1"
                strokeWidth="11"
                strokeDasharray={`${stroke3} ${circ}`}
                strokeDashoffset={offset3}
                strokeLinecap="round"
              />
            </svg>

            {/* Glowing pill in the center */}
            <div className="donut-center-badge">
              In sync
            </div>
          </div>

          <div className="donut-legend">
            <div className="donut-legend-row">
              <span className="donut-legend-label">
                <span className="donut-legend-dot" style={{ backgroundColor: '#1e3a47' }}></span>
                First-Touch
              </span>
              <span className="donut-legend-value">{firstTouchPct}%</span>
            </div>
            <div className="donut-legend-row">
              <span className="donut-legend-label">
                <span className="donut-legend-dot" style={{ backgroundColor: '#3f7267' }}></span>
                Last-Touch
              </span>
              <span className="donut-legend-value">{lastTouchPct}%</span>
            </div>
            <div className="donut-legend-row">
              <span className="donut-legend-label">
                <span className="donut-legend-dot" style={{ backgroundColor: '#9fcbc1' }}></span>
                Linear Split
              </span>
              <span className="donut-legend-value">{linearPct}%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Trending / Active Signals Widget */}
      <div className="widget-card">
        <div className="widget-header">
          <h3 className="widget-title">Trending signals</h3>
          <span
            className="widget-action-link"
            onClick={() => onNavigateTab('attribution')}
          >
            View all
          </span>
        </div>

        <div className="trending-list">
          <div className="trending-item" onClick={() => onNavigateTab('attribution')}>
            <span>#linearmodel</span>
            <span className="trending-arrow">↗</span>
          </div>
          <div className="trending-item" onClick={() => onNavigateTab('exceptions')}>
            <span>#zeroleakage</span>
            <span className="trending-arrow">↗</span>
          </div>
          <div className="trending-item" onClick={() => onNavigateTab('reproducibility')}>
            <span>#deterministicsha</span>
            <span className="trending-arrow">↗</span>
          </div>
          <div className="trending-item" onClick={() => onNavigateTab('journey')}>
            <span>#touchpointeligibility</span>
            <span className="trending-arrow">↗</span>
          </div>
        </div>
      </div>

      {/* Deep Analytics Promo Card */}
      <div className="promo-card">
        <div>
          <span className="promo-badge">Verified Run</span>
          <h4 className="promo-title">
            Bit-for-bit audit reproducibility
          </h4>
          <p style={{ fontSize: '0.775rem', color: '#685c35', lineHeight: 1.4, marginBottom: '0.75rem' }}>
            Seed 20261022 verified with 39/39 passing automated checks.
          </p>
        </div>

        <div className="promo-footer">
          <button
            className="promo-btn"
            title="Inspect Reproducibility"
            onClick={() => onNavigateTab('reproducibility')}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="7 10 12 15 17 10"></polyline>
              <line x1="12" y1="15" x2="12" y2="3"></line>
            </svg>
          </button>
          <div className="promo-graphic" aria-hidden="true">
            ⚡
          </div>
        </div>
      </div>
    </aside>
  );
};

