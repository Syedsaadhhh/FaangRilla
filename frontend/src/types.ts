export interface Event {
  event_id: string;
  title: string;
  venue: string;
  starts_at: string;
  readiness_deadline: string;
  timezone: string;
}

export interface AccommodationPlan {
  plan_id: string;
  event_id: string;
  attendee_alias: string;
  functional_need: string;
  service_type: string;
  language: string;
  format: string;
  equipment: string;
  consent_scope: string[];
  budget_ceiling: number;
  assigned_provider_id: string | null;
  status: string;
  version: number;
}

export interface Provider {
  provider_id: string;
  display_name: string;
  service_types: string[];
  languages: string[];
  formats: string[];
  equipment_supported: string[];
  qualifications: string[];
  cost: number;
  approved: boolean;
  contact_channel: string;
}

export interface RecoveryCase {
  case_id: string;
  event_id: string;
  plan_id: string;
  trigger_type: string;
  trigger_text: string;
  state: string;
  opened_at: string | null;
  response_deadline: string | null;
  recovered_at: string | null;
  confirmed_at: string | null;
  attempt_count: number;
  idempotency_key: string | null;
  blocked_reason: string | null;
  human_decision_required: boolean;
}

export interface AuditEvent {
  audit_id: string;
  case_id: string;
  timestamp: string;
  actor_type: string;
  action: string;
  tool_name?: string | null;
  policy_result?: string | null;
  before_state?: string | null;
  after_state?: string | null;
  correlation_id: string;
  metadata: Record<string, any>;
}

export interface DemoEventData {
  event: Event;
  plan: AccommodationPlan;
  case: RecoveryCase;
  providers: Provider[];
  recent_outbox: Array<{
    offer_id: string;
    case_id: string;
    provider_id: string;
    provider_name: string;
    sent_at: string;
    expires_at: string;
    raw_token: string;
    response_url: string;
    disclosed_fields: Record<string, string>;
  }>;
}

export interface TimelineData {
  case_id: string;
  current_state: string;
  opened_at: string | null;
  recovered_at: string | null;
  confirmed_at: string | null;
  time_to_recovered_seconds: number | null;
  time_to_confirmed_seconds: number | null;
  audit_events: AuditEvent[];
}
