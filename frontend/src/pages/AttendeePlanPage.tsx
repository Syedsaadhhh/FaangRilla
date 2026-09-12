import React, { useState } from 'react';
import { DemoEventData } from '../types';
import { confirmAttendee } from '../api';

interface Props {
  demoData: DemoEventData | null;
  onRefresh: () => void;
  onNavigate: (page: string) => void;
}

export const AttendeePlanPage: React.FC<Props> = ({ demoData, onRefresh, onNavigate }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!demoData) {
    return <div className="card">Loading accommodation plan...</div>;
  }

  const { plan, case: currentCase, providers } = demoData;
  const assignedProvider = providers.find((p) => p.provider_id === plan.assigned_provider_id);

  const handleConfirmRecovery = async () => {
    setLoading(true);
    setError(null);
    try {
      await confirmAttendee(currentCase.case_id);
      onRefresh();
      onNavigate('case');
    } catch (err: any) {
      setError(err.message || 'Failed to confirm recovery');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main>
      <div className="card">
        <span className="synthetic-badge">Attendee Private Plan</span>
        <h1 style={{ marginTop: '0.25rem' }}>Personal Accommodation Plan: {plan.attendee_alias}</h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          Plan Version: <strong>v{plan.version}</strong> &bull; Status:{' '}
          <span className={`status-badge status-${plan.status.toLowerCase().replace(/_/g, '-')}`}>
            {plan.status}
          </span>
        </p>
      </div>

      {error && (
        <div className="card" style={{ borderColor: 'var(--status-red)', color: 'var(--status-red)' }}>
          {error}
        </div>
      )}

      <div className="card">
        <h2>Requested Functional Accommodation</h2>
        <div style={{ marginTop: '0.5rem', lineHeight: '1.8' }}>
          <p>
            <strong>Functional Access Need:</strong> {plan.functional_need}
          </p>
          <p>
            <strong>Service Type:</strong> {plan.service_type}
          </p>
          <p>
            <strong>Technical Format:</strong> {plan.format}
          </p>
          <p>
            <strong>Language:</strong> {plan.language}
          </p>
          <p>
            <strong>Venue Equipment:</strong> {plan.equipment}
          </p>
          <p>
            <strong>Authorized Budget Ceiling:</strong> ${plan.budget_ceiling.toFixed(2)}
          </p>
        </div>
      </div>

      <div className="card">
        <h2>Privacy &amp; Data Minimization Notice</h2>
        <div style={{ background: '#F9FAFB', border: '1px solid var(--border-color)', borderRadius: '6px', padding: '1rem', marginTop: '0.5rem' }}>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
            <strong>Authorized Provider Disclosure Scope:</strong> Only functional operational details (
            {plan.consent_scope.join(', ')}) are shared with providers.
          </p>
          <p style={{ fontSize: '0.9rem', color: '#B91C1C', marginTop: '0.5rem', fontWeight: 500 }}>
            Strict Privacy Guarantee: No medical diagnoses, health histories, or disability classifications are ever requested, inferred, or stored.
          </p>
        </div>
      </div>

      <div className="card">
        <h2>Provider Assignment Status</h2>
        <p>
          <strong>Current Provider:</strong> {assignedProvider ? assignedProvider.display_name : 'Pending assignment'}
        </p>
        <p style={{ marginTop: '0.5rem' }}>
          <strong>Service Cost:</strong> {assignedProvider ? `$${assignedProvider.cost.toFixed(2)}` : 'N/A'}
        </p>

        {currentCase.state === 'ATTENDEE_CONFIRMATION_PENDING' && (
          <div style={{ marginTop: '1.5rem', background: '#F0FDF4', border: '1px solid #86EFAC', borderRadius: '6px', padding: '1.25rem' }}>
            <h3 style={{ color: '#166534', marginBottom: '0.5rem' }}>Replacement Ready for Your Review</h3>
            <p style={{ color: '#166534', marginBottom: '1rem' }}>
              Provider B ({assignedProvider?.display_name}) has accepted the request with exact matching specifications.
            </p>
            <button
              className="btn btn-teal"
              onClick={handleConfirmRecovery}
              disabled={loading}
            >
              {loading ? 'Confirming...' : 'Confirm Replacement Provider'}
            </button>
          </div>
        )}

        {currentCase.state === 'ATTENDEE_CONFIRMED' && (
          <div style={{ marginTop: '1rem', color: 'var(--status-green)', fontWeight: 600 }}>
            &check; You have confirmed this accommodation. The recovery loop is complete.
          </div>
        )}
      </div>
    </main>
  );
};
