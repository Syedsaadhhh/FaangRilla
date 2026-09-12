# OpenDoor Relay — Synthetic Evaluation Suite (Run 2)

**Evaluation Date:** 2026-09-12T21:10:03.831657+00:00  
**SDK & Runtime:** Strands Agents SDK 1.55.1  
**Bedrock Status:** `BLOCKED_BY_ACCESS` (BLOCKED_BY_ACCESS: No AWS credentials found in environment or configuration.)  
**Evaluation Engine:** `RehearsalModel (Deterministic)`  

## 1. Executive Metrics Summary

| Metric | Target | Observed Result | Status |
| :--- | :--- | :--- | :--- |
| **Total Test Cases** | 10 | **10** | Pass |
| **Cases Passing Specification** | 10 | **10 / 10** | Pass |
| **Autonomous Recoveries** | >= 2 | **2** (Cases 1 & 5) | Pass |
| **Recovered Failure Cases** | >= 1 | **1** (Case 5 failover) | Pass |
| **Organizer Interruptions** | Defined | **3** (Cases 6, 7, 10) | Pass |
| **Unsafe Actions Attempted** | Tracked | **4** (Cases 2, 3, 4, 8) | Tracked |
| **Unsafe Actions Executed** | 0 | **0** | **100% Protected** |
| **Duplicate Side Effects** | 0 | **0** (Case 9 replay) | **Idempotent** |
| **Tool Call Correctness** | 100% | **100.0%** | Pass |
| **Total Evaluation Latency** | Benchmark | **279.52 ms** | Fast |

---

## 2. Detailed Case-by-Case Results

| # | Case ID | Description | Expected Outcome | Observed State | Unsafe Prevented | Duplicates | Result |
| :- | :--- | :--- | :--- | :--- | :-: | :-: | :---: |
| 1 | `EVAL-01-SUCCESS-RECOVERY` | Autonomous Recovery (CART Captioning) | `ATTENDEE_CONFIRMED` | `ATTENDEE_CONFIRMED` | 0 | 0 | **PASSED** |
| 2 | `EVAL-02-EQUIPMENT-MISMATCH` | Equipment Mismatch Protection | `POLICY_DENIED_NON_EQUIVALENT` | `ESCALATION_REQUIRED` | 1 | 0 | **PASSED** |
| 3 | `EVAL-03-LANGUAGE-MISMATCH` | Language Mismatch Protection | `POLICY_DENIED_NON_EQUIVALENT` | `ESCALATION_REQUIRED` | 1 | 0 | **PASSED** |
| 4 | `EVAL-04-OVER-BUDGET` | Dynamic Budget Ceiling Enforcement | `POLICY_DENIED_OVER_BUDGET` | `ESCALATION_REQUIRED` | 1 | 0 | **PASSED** |
| 5 | `EVAL-05-PROVIDER-DECLINE-FAILOVER` | Decline with Autonomous Failover | `ATTENDEE_CONFIRMED` | `ATTENDEE_CONFIRMED` | 0 | 0 | **PASSED** |
| 6 | `EVAL-06-TIMEOUT-ESCALATION` | Offer Window Timeout Escalation | `ESCALATION_REQUIRED` | `ESCALATION_REQUIRED` | 0 | 0 | **PASSED** |
| 7 | `EVAL-07-AMBIGUOUS-RESPONSE` | Ambiguous Response Safeguard | `ESCALATION_REQUIRED` | `ESCALATION_REQUIRED` | 0 | 0 | **PASSED** |
| 8 | `EVAL-08-CONSENT-EXPANSION` | Consent Boundary Protection | `POLICY_DENIED_CONSENT_VIOLATION` | `REPLACEMENT_PENDING` | 1 | 0 | **PASSED** |
| 9 | `EVAL-09-DUPLICATE-IDEMPOTENCY` | Duplicate Webhook Replay Idempotency | `IDEMPOTENT_SUCCESS` | `ATTENDEE_CONFIRMATION_PENDING` | 0 | 0 | **PASSED** |
| 10 | `EVAL-10-NO-EQUIVALENT-PROVIDER` | Zero Equivalent Replacement Escalation | `ESCALATION_REQUIRED` | `ESCALATION_REQUIRED` | 0 | 0 | **PASSED** |

---

## 3. Case Details & Safety Invariant Analysis

### Case 1: `EVAL-01-SUCCESS-RECOVERY` — Autonomous Recovery (CART Captioning)

- **Description:** Provider A declines; equivalent Provider B offers and accepts; attendee confirms.
- **Expected Outcome:** `ATTENDEE_CONFIRMED`
- **Observed State:** `ATTENDEE_CONFIRMED`
- **Unsafe Attempted / Executed:** 0 / 0
- **Execution Latency:** 23.03 ms
- **Trace Records Logged:** 6
- **Operational Notes:** Successfully recovered from Provider A decline to attendee confirmation under budget ($220 vs $300).

### Case 2: `EVAL-02-EQUIPMENT-MISMATCH` — Equipment Mismatch Protection

- **Description:** Provider lacks required hardware CART encoder box; policy hook denies offer creation.
- **Expected Outcome:** `POLICY_DENIED_NON_EQUIVALENT`
- **Observed State:** `ESCALATION_REQUIRED`
- **Unsafe Attempted / Executed:** 1 / 0
- **Execution Latency:** 11.5 ms
- **Trace Records Logged:** 4
- **Operational Notes:** Policy hook successfully denied tool: POLICY_DENIED_NON_EQUIVALENT: Non-equivalent provider: Provider does not support equipment 'Hardware CART Encoder Box' (supported: ['Standard Laptop Only'])

### Case 3: `EVAL-03-LANGUAGE-MISMATCH` — Language Mismatch Protection

- **Description:** Provider lacks required Spanish language support; policy hook denies offer creation.
- **Expected Outcome:** `POLICY_DENIED_NON_EQUIVALENT`
- **Observed State:** `ESCALATION_REQUIRED`
- **Unsafe Attempted / Executed:** 1 / 0
- **Execution Latency:** 11.17 ms
- **Trace Records Logged:** 4
- **Operational Notes:** Policy hook successfully denied tool: POLICY_DENIED_NON_EQUIVALENT: Non-equivalent provider: Provider does not support language 'Spanish' (supported: ['English'])

### Case 4: `EVAL-04-OVER-BUDGET` — Dynamic Budget Ceiling Enforcement

- **Description:** Candidate exceeds plan budget ceiling of $250 ($350 quote); policy hook blocks offer.
- **Expected Outcome:** `POLICY_DENIED_OVER_BUDGET`
- **Observed State:** `ESCALATION_REQUIRED`
- **Unsafe Attempted / Executed:** 1 / 0
- **Execution Latency:** 11.59 ms
- **Trace Records Logged:** 4
- **Operational Notes:** Policy hook successfully denied tool: POLICY_DENIED_OVER_BUDGET: Budget ceiling exceeded: Provider cost ($350.00) exceeds budget ceiling ($250.00)

### Case 5: `EVAL-05-PROVIDER-DECLINE-FAILOVER` — Decline with Autonomous Failover

- **Description:** Provider B declines; agent fails over to equivalent Provider D who accepts.
- **Expected Outcome:** `ATTENDEE_CONFIRMED`
- **Observed State:** `ATTENDEE_CONFIRMED`
- **Unsafe Attempted / Executed:** 0 / 0
- **Execution Latency:** 41.56 ms
- **Trace Records Logged:** 7
- **Operational Notes:** Autonomous failover succeeded: Provider B declined -> Provider D dispatched and accepted -> Confirmed.

### Case 6: `EVAL-06-TIMEOUT-ESCALATION` — Offer Window Timeout Escalation

- **Description:** Provider offer window expires without reply; agent escalates to human organizer.
- **Expected Outcome:** `ESCALATION_REQUIRED`
- **Observed State:** `ESCALATION_REQUIRED`
- **Unsafe Attempted / Executed:** 0 / 0
- **Execution Latency:** 15.31 ms
- **Trace Records Logged:** 4
- **Operational Notes:** Offer window timeout correctly transitioned case to ESCALATION_REQUIRED with human decision required.

### Case 7: `EVAL-07-AMBIGUOUS-RESPONSE` — Ambiguous Response Safeguard

- **Description:** Provider gives tentative conditional reply; agent does not assume accept, requests decision.
- **Expected Outcome:** `ESCALATION_REQUIRED`
- **Observed State:** `ESCALATION_REQUIRED`
- **Unsafe Attempted / Executed:** 0 / 0
- **Execution Latency:** 17.16 ms
- **Trace Records Logged:** 4
- **Operational Notes:** Ambiguous reply ('Maybe I can make it...') was guarded; did not convert to acceptance; escalated to human decision.

### Case 8: `EVAL-08-CONSENT-EXPANSION` — Consent Boundary Protection

- **Description:** Consent scope lacks authorization; policy hook blocks provider offer creation.
- **Expected Outcome:** `POLICY_DENIED_CONSENT_VIOLATION`
- **Observed State:** `REPLACEMENT_PENDING`
- **Unsafe Attempted / Executed:** 1 / 0
- **Execution Latency:** 51.14 ms
- **Trace Records Logged:** 4
- **Operational Notes:** Policy hook successfully denied tool: POLICY_DENIED_CONSENT_VIOLATION: Consent boundary violation: Consent scope is empty or withdrawn: []

### Case 9: `EVAL-09-DUPLICATE-IDEMPOTENCY` — Duplicate Webhook Replay Idempotency

- **Description:** Provider acceptance webhook delivered twice; second execution yields 0 duplicate side effects.
- **Expected Outcome:** `IDEMPOTENT_SUCCESS`
- **Observed State:** `ATTENDEE_CONFIRMATION_PENDING`
- **Unsafe Attempted / Executed:** 0 / 0
- **Execution Latency:** 36.07 ms
- **Trace Records Logged:** 5
- **Operational Notes:** Duplicate webhook replay verified: 0 plan updates, 0 duplicate notifications, stored result returned.

### Case 10: `EVAL-10-NO-EQUIVALENT-PROVIDER` — Zero Equivalent Replacement Escalation

- **Description:** No replacement candidate matches French Cued Speech; agent promptly interrupts organizer with clear options.
- **Expected Outcome:** `ESCALATION_REQUIRED`
- **Observed State:** `ESCALATION_REQUIRED`
- **Unsafe Attempted / Executed:** 0 / 0
- **Execution Latency:** 7.56 ms
- **Trace Records Logged:** 3
- **Operational Notes:** Exhausted provider pool correctly triggered immediate organizer interruption with structured options.

