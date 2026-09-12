import React, { useEffect, useState } from 'react';
import { DemoEventData } from './types';
import { fetchDemoEvent, resetDemo } from './api';
import { BRAND_CONFIG } from './config/brand';
import { EventPage } from './pages/EventPage';
import { AttendeePlanPage } from './pages/AttendeePlanPage';
import { ProviderResponsePage } from './pages/ProviderResponsePage';
import { RecoveryCasePage } from './pages/RecoveryCasePage';

export const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<'event' | 'plan' | 'respond' | 'case'>('event');
  const [demoData, setDemoData] = useState<DemoEventData | null>(null);
  const [loading, setLoading] = useState(true);
  const [resetting, setResetting] = useState(false);

  const loadData = async () => {
    try {
      const data = await fetchDemoEvent();
      setDemoData(data);
    } catch (err) {
      console.error('Error loading demo event data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();

    // Check if URL has token in path (e.g. /provider/respond/:token)
    const pathname = window.location.pathname;
    if (pathname.startsWith('/provider/respond/')) {
      setCurrentPage('respond');
    }
  }, []);

  const handleReset = async () => {
    setResetting(true);
    try {
      await resetDemo();
      await loadData();
      setCurrentPage('event');
    } catch (err) {
      console.error('Reset failed:', err);
    } finally {
      setResetting(false);
    }
  };

  return (
    <div className="app-layout">
      <header>
        <div className="logo">
          <span style={{ fontSize: '1.4rem' }}>🛡️</span>
          <span>{BRAND_CONFIG.productName}</span>
          {BRAND_CONFIG.isProvisional && (
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 'normal', marginLeft: '4px' }}>
              (Provisional)
            </span>
          )}
        </div>

        <nav aria-label="Main Navigation">
          <ul className="nav-links">
            <li>
              <button
                className={`nav-btn ${currentPage === 'event' ? 'active' : ''}`}
                onClick={() => setCurrentPage('event')}
              >
                Event
              </button>
            </li>
            <li>
              <button
                className={`nav-btn ${currentPage === 'plan' ? 'active' : ''}`}
                onClick={() => setCurrentPage('plan')}
              >
                Attendee Plan
              </button>
            </li>
            <li>
              <button
                className={`nav-btn ${currentPage === 'respond' ? 'active' : ''}`}
                onClick={() => setCurrentPage('respond')}
              >
                Provider Portal
              </button>
            </li>
            <li>
              <button
                className={`nav-btn ${currentPage === 'case' ? 'active' : ''}`}
                onClick={() => setCurrentPage('case')}
              >
                Recovery Case
              </button>
            </li>
          </ul>
        </nav>

        <div>
          <button
            className="btn btn-outline"
            style={{ fontSize: '0.85rem', padding: '0.4rem 0.8rem' }}
            onClick={handleReset}
            disabled={resetting}
          >
            {resetting ? 'Resetting...' : '↺ Reset Demo'}
          </button>
        </div>
      </header>

      <div className="container">
        {loading ? (
          <div className="card">Loading {BRAND_CONFIG.productName} environment...</div>
        ) : (
          <>
            {currentPage === 'event' && (
              <EventPage demoData={demoData} onRefresh={loadData} onNavigate={(p: any) => setCurrentPage(p)} />
            )}
            {currentPage === 'plan' && (
              <AttendeePlanPage demoData={demoData} onRefresh={loadData} onNavigate={(p: any) => setCurrentPage(p)} />
            )}
            {currentPage === 'respond' && (
              <ProviderResponsePage
                demoData={demoData}
                onRefresh={loadData}
                onNavigate={(p: any) => setCurrentPage(p)}
              />
            )}
            {currentPage === 'case' && (
              <RecoveryCasePage demoData={demoData} onRefresh={loadData} onNavigate={(p: any) => setCurrentPage(p)} />
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default App;
