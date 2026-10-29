import React, { useEffect, useState } from 'react';
import { fetchCustomerJourney } from '../api';
import { CustomerJourneyData } from '../types';

export const JourneyPage: React.FC = () => {
  const [contactId, setContactId] = useState<string>('CON-000262');
  const [searchInput, setSearchInput] = useState<string>('CON-000262');
  const [journey, setJourney] = useState<CustomerJourneyData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadJourney(contactId);
  }, [contactId]);

  async function loadJourney(id: string) {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchCustomerJourney(id);
      setJourney(data);
    } catch (err: any) {
      setError(`Contact journey for '${id}' could not be loaded. Please ensure a valid contact ID is provided.`);
      setJourney(null);
    } finally {
      setLoading(false);
    }
  }

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (searchInput.trim()) {
      setContactId(searchInput.trim());
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Search Header */}
      <div className="card">
        <form onSubmit={handleSearch} style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <label style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--text-primary)' }}>
            Search Customer Journey:
          </label>
          <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="e.g. CON-000001 or CON-000262"
              style={{ width: '280px', borderRadius: 'var(--radius-pill)', paddingLeft: '1rem' }}
            />
          </div>
          <button type="submit" className="btn-primary">
            Trace Journey
          </button>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Try{' '}
            <button
              type="button"
              onClick={() => { setSearchInput('CON-000262'); setContactId('CON-000262'); }}
              style={{ background: 'var(--bg-canvas-subtle)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-pill)', padding: '0.2rem 0.5rem', cursor: 'pointer', color: 'var(--accent-dark)', fontWeight: 600, fontSize: '0.775rem' }}
            >
              CON-000262
            </button>{' '}
            (injected anomaly) or{' '}
            <button
              type="button"
              onClick={() => { setSearchInput('CON-000001'); setContactId('CON-000001'); }}
              style={{ background: 'var(--bg-canvas-subtle)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-pill)', padding: '0.2rem 0.5rem', cursor: 'pointer', color: 'var(--accent-dark)', fontWeight: 600, fontSize: '0.775rem' }}
            >
              CON-000001
            </button>
          </span>
        </form>
      </div>

      {loading && <div style={{ padding: '2.5rem', textAlign: 'center', color: 'var(--text-secondary)' }}>Loading customer journey trace...</div>}

      {error && (
        <div className="banner-warning" style={{ backgroundColor: '#fef2f2', borderColor: '#fca5a5', color: '#b91c1c' }}>
          {error}
        </div>
      )}

      {journey && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Contact Profile Summary */}
          <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <div style={{ width: 48, height: 48, borderRadius: '50%', backgroundColor: 'var(--accent-dark)', color: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: '1.1rem' }}>
                {journey.full_name.split(' ').map((n) => n[0]).join('').substring(0, 2)}
              </div>
              <div>
                <div style={{ fontSize: '1.25rem', fontWeight: 700, letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
                  {journey.full_name}
                </div>
                <div className="mono" style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginTop: '0.15rem' }}>
                  {journey.contact_id} • {journey.email}
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center' }}>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600, letterSpacing: '0.04em' }}>
                  Lifecycle
                </div>
                <div style={{ fontWeight: 700, color: 'var(--text-primary)', marginTop: '0.15rem' }}>{journey.lifecycle_stage}</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600, letterSpacing: '0.04em' }}>
                  Touchpoints
                </div>
                <div style={{ fontWeight: 700, color: 'var(--text-primary)', marginTop: '0.15rem' }}>{journey.total_touchpoints}</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600, letterSpacing: '0.04em' }}>
                  Orders
                </div>
                <div style={{ fontWeight: 700, color: 'var(--text-primary)', marginTop: '0.15rem' }}>{journey.total_orders}</div>
              </div>
            </div>
          </div>

          {/* Chronological Timeline */}
          <div className="card">
            <div style={{ marginBottom: '1.25rem' }}>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 700, letterSpacing: '-0.01em', color: 'var(--text-primary)' }}>
                Chronological Customer Interaction Stream
              </h3>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Sequenced omni-channel events verified under 6-point eligibility rules
              </p>
            </div>

            <div className="timeline">
              {journey.timeline.map((item, idx) => {
                const isExcluded = item.is_eligible_touch === false;
                return (
                  <div key={item.event_id || idx} className="timeline-item">
                    <div className={`timeline-marker ${isExcluded ? 'excluded' : ''}`}>
                      {item.event_type === 'touchpoint' ? '🎯' : item.event_type === 'session' ? '🌐' : item.event_type === 'lead' ? '👤' : item.event_type === 'opportunity' ? '💼' : item.event_type === 'order' ? '🛒' : '⚡'}
                    </div>

                    <div className="timeline-content" style={{ borderColor: isExcluded ? '#fca5a5' : 'var(--border-color)', backgroundColor: isExcluded ? '#fffafa' : '#ffffff' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.4rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{item.title}</span>
                          <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{item.event_id}</span>
                        </div>
                        <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                          {new Date(item.occurred_at).toLocaleString()}
                        </span>
                      </div>

                      {/* Post-conversion or eligibility exclusion warning */}
                      {isExcluded && (
                        <div style={{ marginTop: '0.5rem', marginBottom: '0.5rem', backgroundColor: '#fef2f2', border: '1px solid #fecaca', borderRadius: 'var(--radius-sm)', padding: '0.5rem 0.75rem', color: '#b91c1c', fontSize: '0.8rem' }}>
                          🚫 <strong>Excluded From Attribution:</strong> {item.exclusion_reason}
                        </div>
                      )}

                      {/* Event Attributes Drill-down */}
                      {item.details && Object.keys(item.details).length > 0 && (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.5rem', fontSize: '0.8rem' }}>
                          {Object.entries(item.details).map(([k, v]) => (
                            v !== null && v !== undefined && (
                              <span key={k} style={{ background: 'var(--bg-canvas-subtle)', border: '1px solid var(--border-color)', padding: '0.2rem 0.55rem', borderRadius: 'var(--radius-pill)', color: 'var(--text-secondary)' }}>
                                <strong style={{ color: 'var(--text-primary)' }}>{k}:</strong> <span className="mono">{String(v)}</span>
                              </span>
                            )
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
