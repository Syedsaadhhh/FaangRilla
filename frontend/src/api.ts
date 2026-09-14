import { DemoEventData, TimelineData } from './types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

const INITIAL_LOAD_TIMEOUT_MS = 15_000;

export async function fetchHealth(): Promise<{ status: string; mode: string }> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
  return res.json();
}

export async function fetchDemoEvent(): Promise<DemoEventData> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), INITIAL_LOAD_TIMEOUT_MS);

  try {
    const res = await fetch(`${API_BASE}/api/demo/event`, { signal: controller.signal });
    if (!res.ok) throw new Error(`Failed to load demo event: ${res.statusText}`);
    return res.json();
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error('The live demo took too long to respond. Please retry.');
    }
    throw error;
  } finally {
    window.clearTimeout(timeout);
  }
}

export async function triggerProviderFailure(
  caseId: string,
  triggerText: string = 'Provider A declared sudden unavailability 45m before cutoff'
): Promise<any> {
  const res = await fetch(`${API_BASE}/api/cases/${caseId}/provider-failure`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ trigger_text: triggerText }),
  });
  if (!res.ok) throw new Error(`Failed to trigger failure: ${res.statusText}`);
  return res.json();
}

export async function fetchTimeline(caseId: string): Promise<TimelineData> {
  const res = await fetch(`${API_BASE}/api/cases/${caseId}/timeline`);
  if (!res.ok) throw new Error(`Failed to load timeline: ${res.statusText}`);
  return res.json();
}

export async function fetchOfferDetails(token: string): Promise<any> {
  const res = await fetch(`${API_BASE}/api/provider/offer/${token}`);
  if (!res.ok) throw new Error(`Failed to fetch offer: ${res.statusText}`);
  return res.json();
}

export async function respondToOffer(
  token: string,
  action: 'ACCEPT' | 'DECLINE',
  responseText?: string
): Promise<any> {
  const res = await fetch(`${API_BASE}/api/provider/respond/${token}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action, response_text: responseText }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Response failed with status ${res.status}`);
  }
  return res.json();
}

export async function confirmAttendee(caseId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/api/cases/${caseId}/attendee-confirm`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error(`Failed to confirm: ${res.statusText}`);
  return res.json();
}

export async function resetDemo(): Promise<any> {
  const res = await fetch(`${API_BASE}/api/demo/reset`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error(`Failed to reset: ${res.statusText}`);
  return res.json();
}
