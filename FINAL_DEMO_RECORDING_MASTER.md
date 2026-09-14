# OpenDoor Relay — Final Demo Recording Master

**Primary target:** 2:20–2:35
**Hard ceiling:** 5:00
**Recording style:** one clean story, real product actions, minimal slides, no long code walkthroughs
**Judge memory sentence:** **OpenDoor Relay keeps an event accessible when the original plan fails.**

---

## The Demo Strategy

This cut is designed around the strongest short-form hackathon pattern: **human consequence first, product action second, proof third, architecture last**.

The demo should feel like one incident unfolding in real time, not a feature tour.

### What the viewer should understand in under 20 seconds

1. An accessibility provider can cancel at the worst possible moment.
2. That can exclude an attendee from the event.
3. OpenDoor Relay automatically finds a safe replacement under policy constraints.
4. The replacement accepts, the attendee confirms, and the recovery is auditable.

### What NOT to spend time on

- AWS login or deployment commands.
- Reading code line-by-line.
- Long architecture explanations.
- Generic AI language such as “smart dashboard” or “AI assistant”.
- Claiming live Bedrock inference or AgentCore. The deployed agent framework is genuine Strands, but the current model is deterministic rehearsal because Bedrock quota was blocked.
- Claiming real SES delivery unless it has been explicitly re-tested and proven.

---

# MASTER RECORDING FLOW — SCREEN + VOICE SIDE BY SIDE

| Time | What is on screen / exact action | Voiceover | Why this moment matters |
|---|---|---|---|
| **0:00–0:08** | Start directly on the **Event** page. Show the workshop, accessibility commitment, assigned Provider A, and `CONFIRMED` state. No intro slide longer than one second. | **“Forty-five minutes before an event, the accessibility provider cancels. That is not just a scheduling problem — for the attendee depending on that service, the event can become inaccessible.”** | Immediate human consequence. No product jargon yet. |
| **0:08–0:18** | Keep the Event page visible. Briefly frame the product name and accessibility commitment. | **“OpenDoor Relay exists for that exact failure. It keeps the event accessible when the original plan breaks.”** | Deliver the one-sentence memory hook early. |
| **0:18–0:30** | Point to **Continuity Controls**. Click **`Simulate Provider A Decline (45m to cutoff)`**. Let the UI move naturally to the Recovery Case. | **“Here the confirmed provider drops out just before the readiness cutoff. I am triggering that failure now.”** | Real action begins quickly. |
| **0:30–0:48** | On **Recovery Case**, hold on the state, trigger text, recovery attempt count, and **Audit Trail & Policy Log**. Refresh only if needed. | **“The recovery loop starts immediately. This is not a chatbot waiting for instructions — the Strands agent is executing the recovery workflow, while deterministic policy checks control what it is allowed to do.”** | Establish genuine agent behavior without overexplaining. |
| **0:48–1:03** | Keep the audit/policy log visible. If an approved/blocked policy event is visible, point to it. Do not invent a provider name if the UI does not show one. | **“Candidates are filtered against the attendee’s actual requirements, consent scope, and budget. Unsafe or non-compliant options are blocked before they can become a real assignment.”** | Shows trust and bounded autonomy. |
| **1:03–1:10** | Click **`Open Provider Response Portal →`** when the case is `REPLACEMENT_PENDING`. | **“A compliant backup receives a time-bound response path.”** | Transition from agent decision to human-observable action. |
| **1:10–1:27** | On **Provider Portal**, let the offer details load. Show provider, service, language, equipment and expiration. Click **`Accept Assignment`**. | **“This is the provider’s view. The request contains only the operational details needed to deliver the accommodation. The replacement accepts the assignment.”** | Demonstrates the second actor, not just an organizer dashboard. |
| **1:27–1:38** | After acceptance, click **`View Recovery Case →`**. Show the state update and timeline. | **“That acceptance is recorded once, the plan is updated, and the workflow moves to attendee confirmation.”** | Communicates idempotent state transition without jargon overload. |
| **1:38–1:50** | Click **`Attendee Confirmation Required →`**. On **Attendee Plan**, show the new assigned provider and privacy notice. Click **`Confirm Replacement Provider`**. | **“The attendee remains in control of the final accommodation. They can see the replacement, review the plan, and confirm that the recovered arrangement works for them.”** | Human-in-the-loop at the right boundary. |
| **1:50–2:05** | Return automatically to **Recovery Case**. Hold on `ATTENDEE_CONFIRMED`, the recovery metric, and audit trail. | **“Now the case is complete: replacement accepted, attendee confirmed, and every state transition is preserved in the audit trail. The result is not just a green status — it is a verifiable recovery.”** | This is the proof/payoff shot. Give it visual breathing room. |
| **2:05–2:18** | Briefly show the architecture visual or the AWS-backed system proof. Keep this short: React/Vite → API Gateway → Lambda → Strands → DynamoDB, with EventBridge/SES supporting the flow. | **“The frontend is talking to our deployed AWS backend through API Gateway and Lambda, with DynamoDB holding state. The recovery loop uses the genuine Strands Agents SDK. For this submission, model inference is deterministic rehearsal because live Bedrock quota was blocked.”** | Technical credibility + truth boundary in one concise segment. |
| **2:18–2:30** | End on the final `ATTENDEE_CONFIRMED` screen or a clean product/title frame. | **“OpenDoor Relay is built around one promise: when the original accessibility plan fails, the attendee should not lose access with it.”** | Memorable human-centered ending. |

---

# COPY-READY VOICE SCRIPT

Forty-five minutes before an event, the accessibility provider cancels. That is not just a scheduling problem — for the attendee depending on that service, the event can become inaccessible.

OpenDoor Relay exists for that exact failure. It keeps the event accessible when the original plan breaks.

Here the confirmed provider drops out just before the readiness cutoff. I am triggering that failure now.

The recovery loop starts immediately. This is not a chatbot waiting for instructions — the Strands agent is executing the recovery workflow, while deterministic policy checks control what it is allowed to do.

Candidates are filtered against the attendee’s actual requirements, consent scope, and budget. Unsafe or non-compliant options are blocked before they can become a real assignment.

A compliant backup receives a time-bound response path.

This is the provider’s view. The request contains only the operational details needed to deliver the accommodation. The replacement accepts the assignment.

That acceptance is recorded once, the plan is updated, and the workflow moves to attendee confirmation.

The attendee remains in control of the final accommodation. They can see the replacement, review the plan, and confirm that the recovered arrangement works for them.

Now the case is complete: replacement accepted, attendee confirmed, and every state transition is preserved in the audit trail. The result is not just a green status — it is a verifiable recovery.

The frontend is talking to our deployed AWS backend through API Gateway and Lambda, with DynamoDB holding state. The recovery loop uses the genuine Strands Agents SDK. For this submission, model inference is deterministic rehearsal because live Bedrock quota was blocked.

OpenDoor Relay is built around one promise: when the original accessibility plan fails, the attendee should not lose access with it.

---

# RECORDING PRE-FLIGHT

Before pressing Record:

- Pull latest `main`.
- Run the frontend against the deployed API.
- Click **`↺ Reset Demo`**.
- Confirm Event page starts in `CONFIRMED`.
- Confirm Provider A is assigned.
- Confirm `Mode: rehearsal` is visible and expected.
- Close DevTools.
- Close unrelated browser tabs and notifications.
- Use a clean 16:9 capture at 1080p if possible.
- Browser zoom should keep headings, state badges, and action buttons readable without panning.
- Keep mouse movement deliberate and slow.
- Do one silent rehearsal before the recorded take.

---

# EXACT CLICK PATH

1. **Event**
2. **`Simulate Provider A Decline (45m to cutoff)`**
3. **Recovery Case**
4. Wait for / refresh timeline if necessary
5. **`Open Provider Response Portal →`**
6. **`Accept Assignment`**
7. **`View Recovery Case →`**
8. **`Attendee Confirmation Required →`**
9. **`Confirm Replacement Provider`**
10. Final **Recovery Case** → `ATTENDEE_CONFIRMED`

If a state does not appear, stop the recording and reset. Do not improvise around a broken state on camera.

---

# VISUAL EMPHASIS GUIDE

## Shots worth holding for 2–4 seconds

- Initial `CONFIRMED` event with Provider A.
- The click that causes the failure.
- Recovery Case state + audit trail.
- Provider offer details before acceptance.
- Attendee replacement confirmation.
- Final `ATTENDEE_CONFIRMED` state + recovery metric.

## Things to point at while speaking

- State badge.
- Assigned provider.
- Budget ceiling and privacy notice if visible.
- Audit/policy result.
- Offer expiration.
- Final recovery metric.

## Things to avoid zooming into

- Raw IDs.
- Tokens.
- Long JSON.
- Terminal output.
- Package versions.
- Dense code.

The product should remain the hero, not the infrastructure.

---

# HOOK OPTIONS

Use the main hook unless a shorter version fits the edit better.

### Primary hook
**“Forty-five minutes before an event, the accessibility provider cancels. For the attendee depending on that service, the event can become inaccessible.”**

### Ultra-short hook
**“The event is still happening. The accessibility plan just failed.”**

### Outcome-first hook
**“A last-minute provider cancellation should not become an attendee’s exclusion.”**

---

# CLOSING OPTIONS

### Primary close
**“When the original accessibility plan fails, the attendee should not lose access with it.”**

### Short close
**“OpenDoor Relay turns an accessibility failure into a verified recovery.”**

### Product-memory close
**“OpenDoor Relay keeps the event accessible when the original plan fails.”**

---

# HOW TO EXPLAIN THE TECH WITHOUT LOSING THE VIEWER

Do not list services as a résumé. Tie each technical element to what the viewer just saw:

- **Strands Agents SDK** → orchestrates the recovery actions.
- **Policy hooks / deterministic checks** → prevent unsafe or over-budget action.
- **API Gateway + Lambda** → run the deployed backend without a dedicated server.
- **DynamoDB** → persists the case, offers, state changes, and idempotent workflow state.
- **EventBridge Scheduler** → supports bounded offer timeout handling.
- **SES** → is part of the delivery architecture, but live delivery should only be claimed if explicitly verified.
- **Deterministic rehearsal model** → current model path used because Bedrock quota is blocked; this does not replace the Strands agent loop.

One sentence is enough during the main cut. Put deeper technical explanation in the project page, README, or Q&A.

---

# JUDGE / CLASS Q&A — FAST ANSWERS

### “Is this actually autonomous?”
Yes. The recovery sequence is executed through the Strands agent and its tools. Policy boundaries sit outside free-form model choice so unsafe actions can be blocked deterministically.

### “Why does it say rehearsal?”
The Strands orchestration is genuine and deployed. During the sprint, live Bedrock inference was blocked by quota, so the model layer is deterministic rehearsal. We expose that state instead of hiding it.

### “Why not just send a notification to the organizer?”
Because notification does not restore accessibility. OpenDoor Relay evaluates safe replacements, creates an offer, processes the response, updates the plan, and then asks the attendee to confirm the recovered arrangement.

### “What if no safe provider exists?”
The system fails closed and escalates rather than assigning an unqualified or policy-violating replacement.

### “What makes this different from a dashboard?”
The UI is only the observable surface. The important work is the stateful recovery workflow: detection, constrained provider selection, offer dispatch, response processing, plan update, attendee confirmation, and audit evidence.

### “What about privacy?”
The provider view receives only the functional operational details required for the service. The plan explicitly avoids storing or sharing unnecessary medical diagnoses or histories.

---

# EDITING RHYTHM

A strong cut should follow this pattern:

**Problem → Trigger → Autonomous Action → Human Response → Human Confirmation → Proof → Architecture → Promise**

Keep scene changes purposeful. Do not add cinematic filler between product actions. If using one generated visual or architecture frame, use it for only a few seconds and return to the live product.

The best possible demo is not the one with the most screens. It is the one where the viewer understands the stakes, sees the system act, and believes the proof.
