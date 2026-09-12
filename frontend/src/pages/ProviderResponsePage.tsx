import React, { useState, useEffect } from 'react';
import { DemoEventData } from '../types';
import { fetchOfferDetails, respondToOffer } from '../api';

interface Props {
  demoData: DemoEventData | null;
  selectedToken?: string;
  onRefresh: () => void;
  onNavigate: (page: string) => void;
}

export const ProviderResponsePage: React.FC<Props> = ({
  demoData,
  selectedToken,
  onRefresh,
  onNavigate,
}) => {
  const [tokenInput, setTokenInput] = useState<string>(selectedToken || '');
  const [offerDetails, setOfferDetails] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [resultMessage, setResultMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    // If we have token from outbox, pre-populate
    if (selectedToken) {
      setTokenInput(selectedToken);
      loadOffer(selectedToken);
    } else if (demoData?.recent_outbox && demoData.recent_outbox.length > 0) {
      const latest = demoData.recent_outbox[demoData.recent_outbox.length - 1];
      setTokenInput(latest.raw_token);
      loadOffer(latest.raw_token);
    }
  }, [selectedToken, demoData]);

  const loadOffer = async (token: string) => {
    if (!token.trim()) return;
    setLoading(true);
    setErrorMessage(null);
    try {
      const data = await fetchOfferDetails(token.trim());
      setOfferDetails(data);
    } catch (err: any) {
      setOfferDetails(null);
      setErrorMessage(err.message || 'Could not load offer for this token');
    } finally {
      setLoading(false);
    }
  };

  const handleRespond = async (action: 'ACCEPT' | 'DECLINE') => {
    setActionLoading(true);
    setErrorMessage(null);
    setResultMessage(null);
    try {
      const res = await respondToOffer(tokenInput, action);
      setResultMessage(res.message);
      onRefresh();
      // Reload offer details to show updated state
      loadOffer(tokenInput);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to submit response');
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <main>
      <div className="card">
        <span className="synthetic-badge">Provider Response Portal</span>
        <h1 style={{ marginTop: '0.25rem' }}>Secure Tokenized Provider Response</h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          Mobile-friendly single-purpose portal for backup providers to accept or decline urgent accommodation offers.
        </p>
      </div>

      <div className="card">
        <h2>Response Token</h2>
        <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.5rem' }}>
          <input
            type="text"
            value={tokenInput}
            onChange={(e) => setTokenInput(e.target.value)}
            placeholder="Paste single-use token or select from dispatched offers..."
            style={{
              flex: 1,
              padding: '0.6rem',
              borderRadius: '6px',
              border: '1px solid var(--border-color)',
              fontFamily: 'monospace',
              fontSize: '0.9rem',
            }}
          />
          <button className="btn btn-outline" onClick={() => loadOffer(tokenInput)} disabled={loading}>
            {loading ? 'Checking...' : 'Load Offer'}
          </button>
        </div>
      </div>

      {errorMessage && (
        <div className="card" style={{ borderColor: 'var(--status-red)', color: 'var(--status-red)' }}>
          {errorMessage}
        </div>
      )}

      {resultMessage && (
        <div className="card" style={{ borderColor: 'var(--status-green)', color: 'var(--status-green)', background: '#F0FDF4' }}>
          <strong>Status:</strong> {resultMessage}
        </div>
      )}

      {offerDetails && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h2>Urgent Request for {offerDetails.provider_name}</h2>
            <span className={`status-badge status-${offerDetails.offer_state.toLowerCase()}`}>
              {offerDetails.offer_state}
            </span>
          </div>

          <div style={{ marginTop: '1rem', lineHeight: '1.8' }}>
            <p><strong>Event:</strong> {offerDetails.event_title}</p>
            <p><strong>Venue:</strong> {offerDetails.venue}</p>
            <p><strong>Service Type:</strong> {offerDetails.service_type}</p>
            <p><strong>Format:</strong> {offerDetails.format}</p>
            <p><strong>Language:</strong> {offerDetails.language}</p>
            <p><strong>Required Equipment:</strong> {offerDetails.equipment}</p>
            <p><strong>Response Expiration:</strong> {new Date(offerDetails.expires_at).toLocaleTimeString()}</p>
          </div>

          <div style={{ marginTop: '1.5rem', display: 'flex', gap: '1rem' }}>
            <button
              className="btn btn-teal"
              onClick={() => handleRespond('ACCEPT')}
              disabled={actionLoading}
            >
              {actionLoading ? 'Processing...' : 'Accept Assignment'}
            </button>
            <button
              className="btn btn-danger"
              onClick={() => handleRespond('DECLINE')}
              disabled={actionLoading}
            >
              {actionLoading ? 'Processing...' : 'Decline Offer'}
            </button>
          </div>

          {offerDetails.offer_state === 'ACCEPTED' && (
            <div style={{ marginTop: '1rem' }}>
              <button className="btn btn-outline" onClick={() => onNavigate('case')}>
                View Recovery Case &rarr;
              </button>
            </div>
          )}
        </div>
      )}
    </main>
  );
};
