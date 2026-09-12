import React, { useState } from 'react';
import { DemoEventData } from '../types';
import { triggerProviderFailure } from '../api';

interface Props {
  demoData: DemoEventData | null;
  onRefresh: () => void;
  onNavigate: (page: string) => void;
}

export const EventPage: React.FC<Props> = ({ demoData, onRefresh, onNavigate }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!demoData) {
    return <div className="card">Loading event details...</div>;
  }

  const { event, plan, case: currentCase, providers } = demoData;

  const handleTriggerFailure = async () => {
    setLoading(true);
    setError(null);
    try {
      await triggerProviderFailure(
        currentCase.case_id,
        'Provider A declared sudden unavailability 45 minutes before readiness cutoff'
      );
      onRefresh();
      onNavigate('case');
    } catch (err: any) {
      setError(err.message || 'Failed to trigger provider failure');
    } finally {
      setLoading(false);
    }
  };

  const assignedProvider = providers.find((p) => p.provider_id === plan.assigned_provider_id);

  return (
    <main>
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <span className="synthetic-badge">Synthetic Demo Fixture</span>
            <h1>{event.title}</h1>
            <p style={{ color: 'var(--text-secondary)' }}>
              <strong>Venue:</strong> {event.venue} &bull; <strong>Starts at:</strong>{' '}
              {new Date(event.starts_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} &bull;{' '}
              <strong>Readiness Cutoff:</strong>{' '}
              {new Date(event.readiness_deadline).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </p>
          </div>
          <span className={`status-badge status-${currentCase.state.toLowerCase().replace(/_/g, '-')}`}>
            {currentCase.state}
          </span>
        </div>
      </div>

      {error && (
        <div className="card" style={{ borderColor: 'var(--status-red)', color: 'var(--status-red)' }}>
          {error}
        </div>
      )}

      <div className="grid-2">
        <div className="card">
          <h2>Accessibility Commitments</h2>
          <p>
            <strong>Functional Need:</strong> {plan.functional_need}
          </p>
          <p style={{ marginTop: '0.5rem' }}>
            <strong>Required Service:</strong> {plan.service_type} ({plan.format})
          </p>
          <p style={{ marginTop: '0.5rem' }}>
            <strong>Language:</strong> {plan.language} &bull; <strong>Equipment:</strong> {plan.equipment}
          </p>
          <p style={{ marginTop: '0.5rem' }}>
            <strong>Assigned Provider:</strong>{' '}
            {assignedProvider ? assignedProvider.display_name : 'None (Unassigned)'}
          </p>
          <div style={{ marginTop: '1.25rem' }}>
            <button className="btn btn-outline" onClick={() => onNavigate('plan')}>
              View Private Attendee Plan &rarr;
            </button>
          </div>
        </div>

        <div className="card">
          <h2>Continuity Controls</h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>
            Simulate Provider A dropping out 45 minutes before event cutoff to trigger the autonomous recovery loop.
          </p>

          {currentCase.state === 'CONFIRMED' ? (
            <button
              className="btn btn-danger"
              onClick={handleTriggerFailure}
              disabled={loading}
            >
              {loading ? 'Triggering...' : 'Simulate Provider A Decline (45m to cutoff)'}
            </button>
          ) : (
            <div>
              <p style={{ color: 'var(--accent-teal)', fontWeight: 600, marginBottom: '0.75rem' }}>
                Recovery loop is active ({currentCase.state}).
              </p>
              <button className="btn btn-primary" onClick={() => onNavigate('case')}>
                View Recovery Case & Timeline &rarr;
              </button>
            </div>
          )}
        </div>
      </div>
    </main>
  );
};
