import React from 'react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subValue?: string;
  badge?: {
    label: string;
    variant: 'green' | 'blue' | 'amber' | 'red' | 'purple';
  };
}

export const MetricCard: React.FC<MetricCardProps> = ({ title, value, subValue, badge }) => {
  return (
    <div className="card" style={{ padding: '1.25rem 1.35rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.65rem' }}>
        <div className="kpi-title">{title}</div>
        {badge && (
          <span className={`badge badge-${badge.variant}`}>{badge.label}</span>
        )}
      </div>
      <div className="kpi-value">{value}</div>
      {subValue && <div className="kpi-sub">{subValue}</div>}
    </div>
  );
};
