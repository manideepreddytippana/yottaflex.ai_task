import React from 'react';

interface ChartItem {
  label: string;
  firstTouch: number;
  lastTouch: number;
  linear: number;
}

interface SvgBarChartProps {
  data: ChartItem[];
  title?: string;
  currency?: string;
}

export const SvgBarChart: React.FC<SvgBarChartProps> = ({ data, title, currency = '₹' }) => {
  const topData = data.slice(0, 10); // Display top 10 campaigns
  const maxVal = Math.max(
    ...topData.flatMap((d) => [d.firstTouch, d.lastTouch, d.linear]),
    1
  );

  const chartHeight = 260;
  const barWidth = 14;
  const groupSpacing = 32;
  const groupWidth = barWidth * 3 + 8;
  const totalWidth = topData.length * (groupWidth + groupSpacing) + 70;

  return (
    <div className="card" style={{ overflowX: 'auto' }}>
      {title && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.75rem' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.01em' }}>{title}</h3>
          <div style={{ display: 'flex', gap: '1rem', fontSize: '0.8rem' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-secondary)' }}>
              <span style={{ width: 10, height: 10, backgroundColor: '#2563eb', borderRadius: 3 }}></span> First-Touch
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-secondary)' }}>
              <span style={{ width: 10, height: 10, backgroundColor: '#10b981', borderRadius: 3 }}></span> Last-Touch
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-secondary)' }}>
              <span style={{ width: 10, height: 10, backgroundColor: '#f59e0b', borderRadius: 3 }}></span> Linear
            </span>
          </div>
        </div>
      )}

      <svg width={Math.max(totalWidth, 720)} height={chartHeight + 70} style={{ overflow: 'visible' }}>
        {/* Y Axis Grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map((pct, i) => {
          const y = chartHeight - pct * chartHeight + 20;
          const val = Math.round(pct * maxVal);
          return (
            <g key={i}>
              <line x1="55" y1={y} x2={Math.max(totalWidth, 720)} y2={y} stroke="#ebe7dc" strokeDasharray="3 3" strokeWidth="1" />
              <text x="48" y={y + 4} fill="#889196" fontSize="10" fontFamily="var(--font-mono)" textAnchor="end">
                {currency}{(val / 1000).toFixed(0)}k
              </text>
            </g>
          );
        })}

        {/* Groups */}
        {topData.map((d, i) => {
          const x = 65 + i * (groupWidth + groupSpacing);
          const ftHeight = (d.firstTouch / maxVal) * chartHeight;
          const ltHeight = (d.lastTouch / maxVal) * chartHeight;
          const linHeight = (d.linear / maxVal) * chartHeight;

          return (
            <g key={i}>
              {/* First touch bar */}
              <rect
                x={x}
                y={chartHeight - ftHeight + 20}
                width={barWidth}
                height={Math.max(ftHeight, 3)}
                fill="#2563eb"
                rx="4"
              >
                <title>{`First-Touch: ${currency}${d.firstTouch.toLocaleString()}`}</title>
              </rect>

              {/* Last touch bar */}
              <rect
                x={x + barWidth + 3}
                y={chartHeight - ltHeight + 20}
                width={barWidth}
                height={Math.max(ltHeight, 3)}
                fill="#10b981"
                rx="4"
              >
                <title>{`Last-Touch: ${currency}${d.lastTouch.toLocaleString()}`}</title>
              </rect>

              {/* Linear bar */}
              <rect
                x={x + (barWidth + 3) * 2}
                y={chartHeight - linHeight + 20}
                width={barWidth}
                height={Math.max(linHeight, 3)}
                fill="#f59e0b"
                rx="4"
              >
                <title>{`Linear: ${currency}${d.linear.toLocaleString()}`}</title>
              </rect>

              {/* Campaign Label */}
              <text
                x={x + groupWidth / 2}
                y={chartHeight + 42}
                fill="#586166"
                fontSize="10"
                fontWeight="500"
                textAnchor="middle"
                transform={`rotate(-25 ${x + groupWidth / 2} ${chartHeight + 42})`}
              >
                {d.label.length > 13 ? d.label.substring(0, 11) + '..' : d.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
};
