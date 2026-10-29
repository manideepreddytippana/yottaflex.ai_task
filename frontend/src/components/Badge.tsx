import React from 'react';

interface BadgeProps {
  label: string;
  variant?: 'green' | 'blue' | 'amber' | 'red' | 'purple';
}

export const Badge: React.FC<BadgeProps> = ({ label, variant = 'blue' }) => {
  return <span className={`badge badge-${variant}`}>{label}</span>;
};

