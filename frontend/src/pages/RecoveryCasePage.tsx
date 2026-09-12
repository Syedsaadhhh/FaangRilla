import React, { useEffect, useState } from 'react';
import { DemoEventData, TimelineData } from '../types';
import { fetchTimeline } from '../api';

interface Props {
  demoData: DemoEventData | null;
  onRefresh: () => void;
  onNavigate: (page: string) => void;
}

export const RecoveryCasePage: React.FC<Props> = ({ demoData, onRefresh, onNavigate }) => {
  const [timeline, setTimeline] = useState<TimelineData | null>(null);
  const [loading, setLoading] = useState(false);

  const caseId = demoData?.case.case_id;

  const loadTimeline = async () => {
    if (!caseId) return;
    setLoading(true);
    try {
      const data = await fetchTimeline(caseId);
      setTimeline(data);
    } catch (err) {
      console.error('Failed to load timeline', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTimeline();
  }, [caseId, demoData]);

  if (!demoData) {
    return <div className="card">Loading case data...</div>;
  }

  const { case: currentCase } = demoData;

  return (
    <main>
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <span className="synthetic-badge">Active Continuity Case</span>
            <h1 style={{ marginTop: '0.25rem' }}>Recovery Case: {currentCase.case_id}</h1>
            <p style={{ color: 'var(--text-secondary)' }}>
              <strong>Trigger:</strong> {currentCase.trigger_text}
            </p>
          </div>
          <span className={`status-badge status-${currentCase.state.toLowerCase().replace(/_/g, '-')}`}>
            {currentCase.state}
          </span>
        </div>

        {timeline?.time_to_confirmed_seconds !== null && timeline?.time_to_confirmed_seconds !== undefined && (
          <div className="metric-box">
            <p style={{ fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#166534', fontWeight: 700 }}>
              Official Headline Metric: Time to Confirmed Recovery
            </p>
            <div className="metric-number">
              {timeline.time_to_confirmed_seconds.toFixed(2)}s
            </div>
            <p style={{ fontSize: '0.85rem', color: '#15803D' }}>
              <strong>Formula:</strong> <code>confirmed_at - opened_at</code> (original failure to attendee confirmation)
            </p>
            {timeline?.time_to_recovered_seconds !== null && timeline?.time_to_recovered_seconds !== undefined && (
              <p style={{ fontSize: '0.8rem', color: '#166534', marginTop: '0.5rem', borderTop: '1px dashed #BBF7D0', paddingTop: '0.5rem' }}>
                Supporting Internal Metric (Time to Replacement Acceptance): <strong>{timeline.time_to_recovered_seconds.toFixed(2)}s</strong> (<code>recovered_at - opened_at</code>)
              </p>
            )}
          </div>
        )}
      </div>

      <div className="grid-2">
        <div className="card">
          <h2>Case Metadata</h2>
          <div style={{ lineHeight: '1.8', fontSize: '0.95rem' }}>
            <p><strong>Opened At:</strong> {currentCase.opened_at ? new Date(currentCase.opened_at).toLocaleTimeString() : 'N/A'}</p>
            <p><strong>Response Deadline:</strong> {currentCase.response_deadline ? new Date(currentCase.response_deadline).toLocaleTimeString() : 'N/A'}</p>
            <p><strong>Recovered At:</strong> {currentCase.recovered_at ? new Date(currentCase.recovered_at).toLocaleTimeString() : 'Pending'}</p>
            <p><strong>Confirmed At:</strong> {currentCase.confirmed_at ? new Date(currentCase.confirmed_at).toLocaleTimeString() : 'Pending'}</p>
            <p><strong>Recovery Attempts:</strong> {currentCase.attempt_count}</p>
          </div>

          <div style={{ marginTop: '1.25rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {currentCase.state === 'REPLACEMENT_PENDING' && (
              <button className="btn btn-teal" onClick={() => onNavigate('respond')}>
                Open Provider Response Portal &rarr;
              </button>
            )}
            {currentCase.state === 'ATTENDEE_CONFIRMATION_PENDING' && (
              <button className="btn btn-primary" onClick={() => onNavigate('plan')}>
                Attendee Confirmation Required &rarr;
              </button>
            )}
            <button className="btn btn-outline" onClick={() => { onRefresh(); loadTimeline(); }} disabled={loading}>
              {loading ? 'Refreshing...' : 'Refresh Timeline'}
            </button>
          </div>
        </div>

        <div className="card">
          <h2>Audit Trail &amp; Policy Log</h2>
          {(!timeline || timeline.audit_events.length === 0) ? (
            <p style={{ color: 'var(--text-muted)' }}>No audit events recorded yet.</p>
          ) : (
            <ul className="timeline">
              {timeline.audit_events.map((ev) => (
                <li key={ev.audit_id} className="timeline-item">
                  <div className="timeline-dot" />
                  <div className="timeline-time">
                    {new Date(ev.timestamp).toLocaleTimeString()} &bull; {ev.actor_type}
                  </div>
                  <div className="timeline-title">{ev.action}</div>
                  {ev.policy_result && (
                    <div style={{ fontSize: '0.8rem', color: 'var(--accent-teal)', fontWeight: 600 }}>
                      Policy: {ev.policy_result}
                    </div>
                  )}
                  {ev.before_state && ev.after_state && (
                    <div className="timeline-desc">
                      Transition: <code>{ev.before_state}</code> &rarr; <code>{ev.after_state}</code>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </main>
  );
};
