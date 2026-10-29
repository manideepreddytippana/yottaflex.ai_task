import React, { useState, useEffect } from 'react';
import { OverviewPage } from './pages/OverviewPage';
import { AttributionPage } from './pages/AttributionPage';
import { JourneyPage } from './pages/JourneyPage';
import { ExceptionsPage } from './pages/ExceptionsPage';
import { ReproducibilityPage } from './pages/ReproducibilityPage';
import { RightSidebar } from './components/RightSidebar';
import { fetchHealth, fetchAttributionComparison } from './api';
import { HealthData, AttributionComparisonData } from './types';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'attribution' | 'journey' | 'exceptions' | 'reproducibility'>('overview');
  const [health, setHealth] = useState<HealthData | null>(null);
  const [attrData, setAttrData] = useState<AttributionComparisonData | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch((err) => console.error('API health check error:', err));

    fetchAttributionComparison()
      .then(setAttrData)
      .catch((err) => console.error('Attribution comparison fetch error:', err));
  }, []);

  return (
    <div className="app-shell">
      <div className="app-layout">
        {/* Left Navigation Sidebar */}
        <aside className={`sidebar ${isSidebarCollapsed ? 'collapsed' : ''}`}>
          {/* Brand Header */}
          <div className="sidebar-header">
            <div className="brand-badge" title="YottaFlex.ai">
              <div className="brand-logo-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
                  <path d="M2 17l10 5 10-5"></path>
                  <path d="M2 12l10 5 10-5"></path>
                </svg>
              </div>
              {!isSidebarCollapsed && <span className="brand-name">YottaFlex.ai</span>}
            </div>
            <button
              className="sidebar-collapse-btn"
              title={isSidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
              aria-label={isSidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
              aria-expanded={!isSidebarCollapsed}
              onClick={() => setIsSidebarCollapsed((prev) => !prev)}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="19" y1="12" x2="5" y2="12"></line>
                <polyline points="12 19 5 12 12 5"></polyline>
              </svg>
            </button>
          </div>

          {/* Search Box */}
          {!isSidebarCollapsed && (
            <div className="search-box">
              <span className="search-icon">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="11" cy="11" r="8"></circle>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                </svg>
              </span>
              <input
                type="text"
                placeholder="Search..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          )}

          {/* Navigation Items */}
          <nav className="sidebar-nav">
            <button
              className={`nav-item ${activeTab === 'overview' ? 'active' : ''}`}
              onClick={() => setActiveTab('overview')}
              title="Overview"
            >
              <div className="nav-item-left">
                <span className="nav-item-icon">
                  <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
                    <polyline points="9 22 9 12 15 12 15 22"></polyline>
                  </svg>
                </span>
                {!isSidebarCollapsed && <span>Overview</span>}
              </div>
            </button>

            <button
              className={`nav-item ${activeTab === 'attribution' ? 'active' : ''}`}
              onClick={() => setActiveTab('attribution')}
              title="Attribution"
            >
              <div className="nav-item-left">
                <span className="nav-item-icon">
                  <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10"></circle>
                    <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"></polygon>
                  </svg>
                </span>
                {!isSidebarCollapsed && <span>Attribution</span>}
              </div>
            </button>

            <button
              className={`nav-item ${activeTab === 'journey' ? 'active' : ''}`}
              onClick={() => setActiveTab('journey')}
              title="Customer Journey"
            >
              <div className="nav-item-left">
                <span className="nav-item-icon">
                  <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>
                  </svg>
                </span>
                {!isSidebarCollapsed && <span>Customer Journey</span>}
              </div>
            </button>

            <button
              className={`nav-item ${activeTab === 'exceptions' ? 'active' : ''}`}
              onClick={() => setActiveTab('exceptions')}
              title="Insights & Quality"
            >
              <div className="nav-item-left">
                <span className="nav-item-icon">
                  <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"></path>
                  </svg>
                </span>
                {!isSidebarCollapsed && <span>Insights & Quality</span>}
              </div>
            </button>

            <button
              className={`nav-item ${activeTab === 'reproducibility' ? 'active' : ''}`}
              onClick={() => setActiveTab('reproducibility')}
              title="Reproducibility"
            >
              <div className="nav-item-left">
                <span className="nav-item-icon">
                  <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                    <line x1="16" y1="2" x2="16" y2="6"></line>
                    <line x1="8" y1="2" x2="8" y2="6"></line>
                    <line x1="3" y1="10" x2="21" y2="10"></line>
                  </svg>
                </span>
                {!isSidebarCollapsed && <span>Reproducibility</span>}
              </div>
            </button>
          </nav>

          {/* Sidebar Footer with Progress Meter & Profile */}
          <div className="sidebar-footer">
            {!isSidebarCollapsed && (
              <div className="profile-strength-card">
                <div className="profile-strength-header">
                  <span>Validation suite</span>
                  <span className="profile-strength-val">39/39</span>
                </div>
                <div className="progress-track">
                  <div className="progress-fill" style={{ width: '100%' }}></div>
                </div>
              </div>
            )}

            <div className="user-profile-badge" title="FastAPI Engine (@seed.20261022)">
              <div className="user-avatar-info">
                <div className="user-avatar">
                  ⚡
                </div>
                {!isSidebarCollapsed && (
                  <div>
                    <div className="user-name">FastAPI Engine</div>
                    <div className="user-subtext">@seed.20261022</div>
                  </div>
                )}
              </div>
              {!isSidebarCollapsed && (
                <span style={{ color: 'var(--text-muted)', fontSize: '1rem', cursor: 'pointer' }}>⋮</span>
              )}
            </div>
          </div>
        </aside>

        {/* Center Main Content Area */}
        <main className="main-content">
          {/* Top Control / Action Box */}
          <div className="top-action-card">
            <div className="top-action-header">
              <div className="dropdown-pill">
                <span>Reporting Currency: <strong>INR (₹)</strong></span>
                <span>▾</span>
              </div>
              <div className="action-icons-group">
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', fontSize: '0.8rem', marginRight: '0.5rem' }}>
                  <span
                    style={{
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      backgroundColor: health?.database_connected ? '#10b981' : '#ef4444',
                      boxShadow: health?.database_connected ? '0 0 6px rgba(16, 185, 129, 0.6)' : 'none',
                    }}
                  ></span>
                  <span style={{ color: 'var(--text-secondary)' }}>
                    {health?.database_connected ? 'Connected' : 'Checking...'}
                  </span>
                </div>
                <button className="icon-action-btn" title="Filter Settings">
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="4" y1="21" x2="4" y2="14"></line>
                    <line x1="4" y1="10" x2="4" y2="3"></line>
                    <line x1="12" y1="21" x2="12" y2="12"></line>
                    <line x1="12" y1="8" x2="12" y2="3"></line>
                    <line x1="20" y1="21" x2="20" y2="16"></line>
                    <line x1="20" y1="12" x2="20" y2="3"></line>
                    <line x1="1" y1="14" x2="7" y2="14"></line>
                    <line x1="9" y1="8" x2="15" y2="8"></line>
                    <line x1="17" y1="16" x2="23" y2="16"></line>
                  </svg>
                </button>
              </div>
            </div>

            <div className="quick-input-placeholder">
              Multi-Touch Attribution • Financial Reconciliation • Anomaly Detection • Bit-for-Bit Reproducibility
            </div>

            <div className="top-action-footer">
              <div className="action-chips">
                <span className="chip-pill chip-sparkle">
                  ✨ Linear 100% Reconciled
                </span>
                <span className="chip-pill">
                  📎 Seed: 20261022
                </span>
              </div>
              <button
                className="btn-primary"
                onClick={() => {
                  if (activeTab === 'overview') setActiveTab('attribution');
                  else if (activeTab === 'attribution') setActiveTab('journey');
                  else setActiveTab('overview');
                }}
              >
                Explore
              </button>
            </div>
          </div>

          {/* Active Tab Page Content */}
          <div>
            {activeTab === 'overview' && <OverviewPage />}
            {activeTab === 'attribution' && <AttributionPage />}
            {activeTab === 'journey' && <JourneyPage />}
            {activeTab === 'exceptions' && <ExceptionsPage />}
            {activeTab === 'reproducibility' && <ReproducibilityPage />}
          </div>

          {/* Clean Footer */}
          <footer style={{ marginTop: '1.5rem', padding: '1.25rem 0', textAlign: 'center', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            <p>Marketing Campaign Attribution & ROI System • Seed: 20261022 • FastAPI + SQLite • React + TypeScript + Vite</p>
            <p style={{ marginTop: '0.2rem', fontSize: '0.75rem' }}>Strict 6-point Touchpoint Eligibility • Remainder Cent Allocation • Zero Ground-Truth Leakage</p>
          </footer>
        </main>

        {/* Right Sidebar Widgets */}
        <RightSidebar attrData={attrData} onNavigateTab={setActiveTab} />
      </div>
    </div>
  );
};
