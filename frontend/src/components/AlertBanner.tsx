import React from 'react';
import { WeeklySpikeAlert } from '../api';
import { Icon } from './Icons';

interface AlertBannerProps {
  alerts: WeeklySpikeAlert[];
}

function AlertBanner({ alerts }: AlertBannerProps) {
  if (alerts.length === 0) {
    return null;
  }

  return (
    <div className="alert-banner" style={{ animation: 'slideIn 0.5s ease-out' }}>
      <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <Icon name="alertTriangle" size={20} color="#fc8181" />
        Weekly Spike Alerts
      </h3>
      <p style={{ marginBottom: '1rem', color: 'var(--text-secondary)' }}>
        The following topics are experiencing significant increases with high negative sentiment:
      </p>
      {alerts.map((alert, index) => (
        <div key={index} className="alert-item" style={{ animation: `fadeInUp 0.5s ease-out ${index * 0.1}s both` }}>
          <strong>{alert.message}</strong>
          <div style={{ fontSize: '0.9rem', marginTop: '0.5rem', opacity: 0.9 }}>
            Current week: {alert.current_week_count} calls | Last week: {alert.last_week_count} calls
          </div>
        </div>
      ))}
    </div>
  );
}

export default AlertBanner;

