# OpenDoor Relay — Antigravity Execution Boss

**Project:** OpenDoor Relay  
**Hackathon:** Agents for Humans  
**Track:** Good Neighbor Agents  
**Build mode:** Autonomous, five controlled runs  
**Primary runtime:** AWS  
**Build workspace:** Google Antigravity IDE  
**Product lock:** Accessibility continuity for community events  

> **Judge memory sentence:** OpenDoor Relay keeps an event accessible when the original plan fails.

This file is the build contract. Do not reopen ideation, broaden the product into general event management, add a generic AI chat, or include CALL-E. Build and prove one complete recovery loop.

---

## 0. Human setup — do this while Antigravity builds

### Required accounts and access

- [ ] **Devpost:** remain registered for Agents for Humans. We will submit under **Good Neighbor Agents**.
- [ ] **GitHub:** create one new repository named `opendoor-relay`. Keep it private during unstable early work if desired, but it must be **public before submission**.
- [ ] **License:** select **MIT** when creating the repository, or add it during Run 1. The repository About panel and README must both show the license.
- [ ] **AWS account:** an account that can use IAM, Amazon Bedrock, Lambda, API Gateway, DynamoDB, EventBridge Scheduler, CloudWatch, SES, Amplify Hosting, and—if enabled—Bedrock AgentCore.
- [ ] **AWS Builder ID:** record the email/ID required by the Devpost submission form.
- [ ] **AWS CLI:** install and authenticate it on the same computer that runs Antigravity. Use a dedicated least-privilege hackathon identity; do not use root credentials.
- [ ] **Bedrock model access:** in the chosen AWS Region, confirm at least one suitable, affordable text model can be invoked. Prefer `us-east-1` only if Bedrock and AgentCore are available there for this account; otherwise select one region that supports both and use it consistently.
- [ ] **AgentCore:** open the console once and check Runtime access/quota. Do not wait on approval for more than 60 minutes; the Lambda fallback is valid.
- [ ] **Amazon SES:** verify the sender address plus inboxes acting as Provider A and Provider B (three addresses, or fewer if one verified address safely serves multiple demo roles). Sandbox mode is acceptable for the demo.
- [ ] **Recording:** OBS or another screen recorder, a microphone, and a browser profile with no private tabs, keys, or personal notifications visible.

### Values to collect locally

Never paste secret values into this MD, source code, Git, screenshots, chat, or run reports.

```text
AWS_ACCOUNT_ID=
AWS_REGION=
AWS_CLI_PROFILE=
BEDROCK_MODEL_ID=
SES_FROM_EMAIL=
PROVIDER_A_EMAIL=
PROVIDER_B_EMAIL=
GITHUB_REPO_URL=
PUBLIC_APP_URL=
PUBLIC_API_URL=
AWS_BUILDER_ID_EMAIL=
```

Only non-secret examples belong in `.env.example`. Real local values belong in ignored environment files or AWS secret/configuration services.

### Do not buy or create

- No domain is required.
- No paid database is required.
- No Twilio account is required.
- No provider marketplace or payment account is required.
- No additional vector database is required.
- No Cognito setup is required for the public judging demo.
- Do not add SQS, Step Functions, multiple agents, or AgentCore Memory/Gateway unless a demonstrated requirement makes them necessary.

---

## 1. Exact startup procedure in Google Antigravity

1. Create a desktop folder named `OpenDoor-Relay`.
2. Put this file inside that folder with the exact filename `OPENDOOR_RELAY_ANTIGRAVITY_EXECUTION_BOSS.md`.
3. Open **that folder**, not only this file, in Antigravity IDE.
4. Select review-driven terminal permissions. Allow ordinary project commands, but manually review destructive commands, cloud mutations, and anything involving credentials.
5. Open the Antigravity agent panel.
6. Paste the **Master Control Prompt** below first.
7. When Antigravity stops and confirms the contract, paste **Run 1**.
8. Execute only one numbered run at a time. Do not paste all five simultaneously.
9. At the end of every run, open its `RUN_n_REPORT.md`. If acceptance checks pass, continue. If not, bring the report and exact error back to ChatGPT before starting the next run.

### Paste this first — Master Control Prompt

```text
You are the principal engineer and release owner for OpenDoor Relay. Read OPENDOOR_RELAY_ANTIGRAVITY_EXECUTION_BOSS.md completely before taking any action. Treat it as the binding product, safety, architecture, and verification contract.

Rules:
1. Work only in the currently opened OpenDoor-Relay folder.
2. Do not build yet. First inspect the folder, Git status, installed runtimes, AWS CLI availability, and existing files.
3. Never print, copy, commit, or place secrets in reports. Never overwrite a real .env file.
4. Preserve all user work. Do not delete or reset anything without explicit approval.
5. Do not invent successful tests, AWS deployments, emails, traces, timing metrics, or URLs.
6. Use current official AWS and Strands documentation when an SDK or deployment command is version-sensitive. Pin compatible dependency versions after validating them.
7. The agent may interpret language and select among policy-safe actions. Deterministic code must enforce privacy, consent, equivalence, budget, deadlines, idempotency, and state transitions.
8. No diagnosis collection, entitlement decision, legal/medical advice, generic dashboard, primary chat UI, decorative multi-agent swarm, or CALL-E code.
9. Every numbered run ends at its STOP condition. Do not continue into the next run automatically.
10. Before changing files, respond with: detected environment, existing-file status, top three risks, and whether Run 1 is safe to start. Then stop.
```

Expected response: a short environment inventory and **“Run 1 is safe to start”** or one precise blocker. No code should be written yet.

---

## 2. Locked product contract

### Hero scenario

A community workshop has already confirmed live captioning and front-row seating for an attendee. Forty-five minutes before the readiness cutoff, Provider A declines. OpenDoor Relay:

1. receives the decline or detects a timeout;
2. interprets the reply through a Strands agent using Amazon Bedrock;
3. uses deterministic filters to find approved equivalent providers;
4. contacts Provider B and schedules a response deadline;
5. processes Provider B's acceptance idempotently;
6. atomically updates the provider assignment, attendee plan, room checklist, staff task, and run of show;
7. notifies the attendee and records confirmation; and
8. interrupts the organizer only when an equivalent safe recovery is unavailable or a boundary is crossed.

### Required negative path

The agent proposes an option that exceeds the approved budget or is not equivalent. Deterministic policy blocks the action. The product shows a human-readable **Needs your decision** item containing the decision, reason, safe alternatives, deadline, and audit trail. The system must never present the blocked option as completed.

### Primary metric

**Time to confirmed recovery** = timestamp of final attendee-confirmed replacement minus timestamp of original provider failure.

- Start and stop timestamps must be produced by the system.
- Display the metric prominently after the hero run.
- A target such as “under 90 seconds” is not a result. Replace it with the observed measurement.
- Never invent a manual baseline.

### Supporting evaluation

Create ten labeled synthetic cases covering decline, timeout, ambiguous response, equipment mismatch, language mismatch, duplicate response, over-budget option, consent expansion, no equivalent provider, and successful recovery.

Report:

- successful autonomous recoveries;
- recovered failure cases;
- organizer interruptions;
- unsafe actions attempted and executed;
- duplicate side effects;
- tool-call correctness; and
- each failed case with a plain explanation.

### Accessibility and privacy boundaries

- Store functional access needs, not diagnoses.
- Show exactly what information may be disclosed to a provider.
- Never infer disability, eligibility, or medical facts.
- Provide keyboard navigation, visible focus, semantic landmarks, high contrast, screen-reader labels, reduced-motion support, and no color-only status.
- Use synthetic names and events in the public demo.

---

## 3. Target architecture

### Frontend

- React + TypeScript + Vite
- React Router
- Accessible CSS/design tokens; avoid a heavy UI framework unless already installed
- Hosted on AWS Amplify Hosting; S3 + CloudFront or Vercel is an allowed hosting fallback

### Backend and agent

- Python 3.12
- FastAPI for a clear local API contract
- Mangum or a thin Lambda adapter for API Gateway/Lambda
- Strands Agents SDK with an Amazon Bedrock model
- AgentCore Runtime as the preferred judged runtime
- A runtime adapter so the same core orchestration can run locally and through Lambda if AgentCore is blocked

### Durable services

- DynamoDB: authoritative event, case, response, and audit state
- EventBridge Scheduler: one-time provider-response deadlines
- Amazon SES: verified demo emails
- CloudWatch and AgentCore Observability: logs, traces, latency, errors
- AWS CDK in TypeScript: reproducible infrastructure

### Architecture rule

The core business policy must not depend on a UI component, an LLM's prose, or a fake background timer. Tool functions own mutations. Conditional writes and idempotency keys prevent duplicate provider assignments and duplicate notifications.

---

## 4. Domain and API contract

### Minimum entities

```text
Event
- event_id, title, venue, starts_at, readiness_deadline, timezone

AccommodationPlan
- plan_id, event_id, attendee_alias, functional_need, service_type
- language, format, equipment, consent_scope, budget_ceiling
- assigned_provider_id, status, version

Provider
- provider_id, display_name, service_types, languages, formats
- equipment_supported, qualifications, availability_windows
- cost, approved, contact_channel

RecoveryCase
- case_id, event_id, plan_id, trigger_type, trigger_text
- state, opened_at, response_deadline, recovered_at, confirmed_at
- attempt_count, idempotency_key, blocked_reason, human_decision_required

ProviderOffer
- offer_id, case_id, provider_id, state, sent_at, expires_at
- response_at, response_text, response_token_hash

AuditEvent
- audit_id, case_id, timestamp, actor_type, action
- tool_name, policy_result, before_state, after_state, correlation_id
```

### State machine

```text
CONFIRMED -> AT_RISK -> RECOVERING -> REPLACEMENT_PENDING
REPLACEMENT_PENDING -> RECOVERED -> ATTENDEE_CONFIRMATION_PENDING -> ATTENDEE_CONFIRMED
RECOVERING | REPLACEMENT_PENDING -> ESCALATION_REQUIRED
RECOVERING | REPLACEMENT_PENDING -> TIMED_OUT
```

Reject invalid transitions. Retrying the same command must return the stored result without repeating external side effects.

### Minimum API surface

```text
GET    /health
GET    /api/demo/event
POST   /api/cases/{case_id}/provider-failure
GET    /api/cases/{case_id}
GET    /api/cases/{case_id}/timeline
POST   /api/provider/respond/{token}
POST   /api/cases/{case_id}/attendee-confirm
POST   /api/cases/{case_id}/human-decision
POST   /api/demo/reset
GET    /api/evaluation/latest
```

Return typed JSON and stable error codes. Provider response tokens must be random, single-purpose, expiring, stored as hashes, and safe to expose in a URL. The public demo reset endpoint must be rate-limited or protected by a non-secret demo-control mechanism.

### Required agent tools

```text
get_case_context(case_id)
find_eligible_replacements(case_id)
create_provider_offer(case_id, provider_id)
send_provider_offer(offer_id)
schedule_offer_timeout(offer_id)
record_provider_response(offer_id, response)
apply_confirmed_replacement(case_id, offer_id)
notify_attendee(case_id)
request_human_decision(case_id, reason, safe_options)
```

The model cannot directly write DynamoDB, send email, change the budget, expand consent, or force a state transition.

---

# RUN 1 — Foundation and executable vertical slice

**Budget:** approximately 4 focused hours  
**Purpose:** prove the repository, contracts, state machine, and one local end-to-end recovery before styling or cloud work.

### Paste into Antigravity

```text
Execute RUN 1 from OPENDOOR_RELAY_ANTIGRAVITY_EXECUTION_BOSS.md. Work autonomously inside the current folder and stop at the RUN 1 STOP condition.

Build:
1. Initialize Git if needed. Do not change an existing remote without approval. Add MIT license, .gitignore, .editorconfig, README skeleton, SECURITY.md, and .env.example with placeholders only.
2. Scaffold frontend/ (React + TypeScript + Vite), backend/ (Python 3.12 FastAPI), infra/ (AWS CDK TypeScript placeholder), docs/, scripts/, and tests/. Keep a single root README with exact local commands.
3. Define typed domain models, the recovery state machine, deterministic policy results, stable error codes, and idempotency behavior from the boss file.
4. Implement a repository interface plus an in-memory/local implementation. Keep DynamoDB behind the interface for Run 3.
5. Implement a provider-gateway interface with a local inbox adapter. It must create a real response token and provider response URL locally, not pretend to send email.
6. Implement the minimum API endpoints needed for the hero path: health, demo event, provider failure, case read/timeline, provider response, attendee confirmation, and demo reset.
7. Add one seeded synthetic workshop, one attendee plan, Provider A, Provider B, and one intentionally blocked Provider C. Mark all demo data visibly as synthetic.
8. Implement one deterministic local orchestration path: Provider A declines, Provider B is eligible, B accepts, related plan views update, attendee confirms, recovery metric stops.
9. Add unit tests for valid/invalid state transitions, equivalence filtering, budget boundary, consent boundary, token expiry, and duplicate response idempotency.
10. Add scripts/run-local.* appropriate for the operating system and scripts/verify-run-1.* that exercise the hero API path and exit nonzero on failure.

Verification:
- install dependencies using reproducible lock files;
- run backend tests;
- run frontend typecheck/build;
- run the Run 1 verification script against a local backend;
- scan tracked files for likely secrets;
- inspect git diff and git status;
- commit only after checks pass with message: feat: establish OpenDoor Relay vertical slice

Create docs/execution/RUN_1_REPORT.md containing: commit SHA, changed-file summary, exact commands and results, test counts, local URLs, unresolved blockers, intentional substitutions, and the next-run risks. Never include secrets.

RUN 1 STOP CONDITION: Stop after the local hero path passes, the commit exists, and RUN_1_REPORT.md is written. Do not start AWS deployment, SES integration, visual polish, or Run 2.
```

### Human acceptance checkpoint

- [ ] `GET /health` is healthy.
- [ ] The seeded event and attendee plan render as actual pages.
- [ ] A failure, replacement acceptance, plan update, and attendee confirmation can be completed locally.
- [ ] Repeating Provider B's response causes zero duplicate updates.
- [ ] Blocked Provider C cannot be applied.
- [ ] Backend tests and frontend build pass.
- [ ] No secrets are tracked.
- [ ] `docs/execution/RUN_1_REPORT.md` exists with a real commit SHA.

If any item fails, stop and bring the report plus the exact terminal error back here.

---

# RUN 2 — Strands intelligence, safety hooks, failures, and evaluation

**Budget:** approximately 6 focused hours  
**Purpose:** make Strands load-bearing while deterministic code keeps authority.

### Paste into Antigravity

```text
Execute RUN 2 from OPENDOOR_RELAY_ANTIGRAVITY_EXECUTION_BOSS.md. First read RUN_1_REPORT.md and confirm its commit exists. Work autonomously and stop at the RUN 2 STOP condition.

Build:
1. Add the Strands Agents SDK and a configurable Amazon Bedrock model adapter. Pin only versions verified against current official documentation. Preserve a deterministic rehearsal model for tests; label it clearly and never present it as live Bedrock.
2. Write the agent system contract: protect a confirmed accessibility commitment; minimize disclosure; use only approved tools; never determine diagnosis/eligibility; never override policy; request a human decision only for defined exceptions.
3. Register typed tools from the boss file. Tool results must be structured objects, not prose-only success messages.
4. Add hooks around tool calls to validate case state, policy authorization, idempotency key, correlation ID, and audit recording. A denied hook must prevent tool execution.
5. Use the agent for non-trivial language interpretation and recovery sequencing: classify decline/timeout/ambiguous reply, request clarification when needed, select among already policy-eligible options, react to tool results, and decide whether to continue or interrupt.
6. Ensure deterministic code alone filters equivalence, budget, consent, deadlines, qualifications, availability, equipment, and maximum attempts.
7. Implement the decline, timeout, ambiguous reply, no-equivalent, over-budget, consent-expansion, and duplicate-response branches.
8. Create ten versioned synthetic evaluation cases and a repeatable evaluation runner. Persist machine-readable JSON and generate a human-readable summary without inventing results.
9. Add tests proving: a model cannot call a denied tool, an unsafe option is never applied, duplicates have no side effect, ambiguous text does not become acceptance, and a timeout either retries within policy or escalates.
10. Add a developer-only trace view or structured trace export that shows model decision, tool call, policy decision, state transition, and timing without revealing secrets or sensitive chain-of-thought. Summaries and tool evidence are enough; do not expose hidden reasoning.

Verification:
- run the full backend suite and frontend typecheck/build;
- run all ten evaluation cases with the rehearsal model;
- if AWS credentials and model access are ready, run one explicitly labeled live Bedrock smoke test and save sanitized evidence; otherwise record BLOCKED_BY_ACCESS and continue without claiming it passed;
- inspect the trace for one success and one blocked branch;
- run secret scan and dependency audit where practical;
- commit passing work with message: feat: add bounded Strands recovery agent

Create docs/execution/RUN_2_REPORT.md containing: commit SHA, SDK/model configuration excluding secrets, exact test results, evaluation table, live Bedrock status, sanitized success and denied-tool evidence, blockers, and fallback decision.

RUN 2 STOP CONDITION: Stop after Strands drives the tested orchestration, policy blocks unsafe actions, ten-case evaluation artifacts exist, the commit exists, and RUN_2_REPORT.md is written. Do not deploy AWS infrastructure or begin Run 3.
```

### Human acceptance checkpoint

- [ ] Removing the Strands orchestration would break the adaptive recovery flow.
- [ ] Removing model access does not remove safety enforcement.
- [ ] All ten cases produce honest, reviewable results.
- [ ] Unsafe executed actions and duplicate side effects equal zero.
- [ ] One success and one interruption are understandable from the trace.
- [ ] Live Bedrock is either proven or plainly marked blocked—not simulated as live.

---

# RUN 3 — AWS deployment and real external side effects

**Budget:** approximately 7 focused hours  
**Purpose:** convert the local proof into an AWS-native, observable system.

### Fallback timebox

Spend no more than 60 minutes on an AgentCore quota, permission, packaging, or regional blocker. Preserve the same Strands agent and deploy the runtime adapter through Lambda/container if AgentCore cannot be verified. Record the limitation honestly.

### Paste into Antigravity

```text
Execute RUN 3 from OPENDOOR_RELAY_ANTIGRAVITY_EXECUTION_BOSS.md. Read RUN_1_REPORT.md and RUN_2_REPORT.md first. Before cloud mutation, show the planned AWS resources, selected region/profile, estimated cost-sensitive services, and teardown command. Never print credentials. After that brief review, proceed with the approved project architecture and stop at the RUN 3 STOP condition.

Build and deploy:
1. Complete AWS CDK stacks with tags for project=opendoor-relay and environment=hackathon. Use least-privilege roles and configuration parameters instead of hardcoded account values.
2. Provision DynamoDB with conditional-write patterns and TTL where appropriate. Add a DynamoDB repository adapter and contract tests shared with the local adapter.
3. Provision API Gateway + Lambda for the public control API. Configure CORS only for the actual frontend origins and local development origin.
4. Deploy the Strands agent to AgentCore Runtime when available. Add an authenticated server-side invocation adapter. If the 60-minute limit is reached, deploy the same core through the documented Lambda/container fallback and mark AGENTCORE_STATUS=fallback in evidence.
5. Provision EventBridge Scheduler for one-time offer timeouts, with idempotent callback processing, retry policy, and dead-letter/error visibility appropriate to the chosen architecture.
6. Integrate SES using only verified demo addresses in sandbox. Provider emails must contain a tokenized accept/decline/clarify link. If SES is blocked, keep the public response portal real and label the local inbox adapter as fallback.
7. Add CloudWatch structured logs, correlation IDs, latency metrics, error counts, and sanitized agent/tool evidence. Enable AgentCore Observability when AgentCore is used.
8. Add seed and reset commands for synthetic demo data. Reset must never affect non-demo data.
9. Add scripts/verify-aws.* that prove health, DynamoDB persistence, one agent invocation, one scheduled timeout or safely shortened test timeout, one provider response, idempotent replay, and log correlation.
10. Generate docs/architecture.md plus a clean Mermaid source for the final architecture image. Distinguish the live path from fallbacks.

Verification:
- CDK synth passes;
- deployment command exits successfully;
- public health endpoint responds;
- the AWS verification script passes against deployed resources;
- one real SES message is received, or SES is accurately marked blocked with response portal proof;
- one AgentCore invocation is traced, or the timed fallback decision is documented;
- no credentials or account-sensitive output are committed;
- commit passing work with message: feat: deploy durable AWS recovery workflow

Create docs/execution/RUN_3_REPORT.md containing: commit SHA, deployed resource names/regions, public API URL, commands and results, AgentCore status, SES status, sanitized trace identifiers, cost/cleanup notes, blockers, and every fallback used. Do not include account numbers, keys, tokens, or private console URLs.

RUN 3 STOP CONDITION: Stop after the deployed API performs the hero recovery with durable state, evidence is recorded, the commit exists, and RUN_3_REPORT.md is written. Do not perform visual polish or submission work.
```

### Human acceptance checkpoint

- [ ] AWS state survives process restart and browser refresh.
- [ ] At least one genuine external side effect is visible: SES delivery, scheduled wake-up, or both.
- [ ] Duplicate response remains idempotent in AWS.
- [ ] AgentCore is either genuinely proven or honestly replaced by the fallback.
- [ ] Logs connect the failure, tool calls, provider response, state update, and metric with one correlation ID.

---

# RUN 4 — Complete accessible product and judge-visible proof

**Budget:** approximately 7 focused hours  
**Purpose:** turn the working infrastructure into a coherent multi-page product—not a technical dashboard.

### Page contract

1. **Event:** event purpose, time, venue, accessibility commitments, and a clear path to the private plan.
2. **Attendee plan:** confirmed functional service, consent/disclosure summary, provider status, version history, and confirmation action.
3. **Provider response:** tokenized mobile-friendly accept/decline/clarify interaction with expiry and duplicate handling.
4. **Staff run of show:** only operational instructions, room/equipment checklist, owner, deadline, and current confirmed provider.
5. **Recovery case:** human-readable chronological story of what failed, what the agent tried, what changed, and time to confirmed recovery.
6. **Needs your decision:** only genuine policy exceptions with safe choices, reason, deadline, and consequence of no action.

### Paste into Antigravity

```text
Execute RUN 4 from OPENDOOR_RELAY_ANTIGRAVITY_EXECUTION_BOSS.md. Read all prior RUN reports and use the deployed API when available. Work autonomously and stop at the RUN 4 STOP condition.

Build:
1. Implement all six required product pages. The default experience must be a real service workflow, not chat, a cyber dashboard, an admin analytics wall, or cards that merely claim background work happened.
2. Create a restrained premium design system: warm neutral background, deep ink text, accessible indigo/teal actions, one amber exception color, subtle borders, minimal shadow, no glass overload, no neon, and no fake live indicators.
3. Make the recovery case the visual hero. Show a plain-language timeline tied to real audit events, a live deadline, current safe action, and the measured recovery clock.
4. Make provider and attendee pages mobile-first. Keep staff operations scannable. Display only data appropriate to each role.
5. Add loading, empty, expired-token, offline/API-error, retry, timeout, duplicate-response, no-provider, and escalation states. Never silently convert an error into success.
6. Meet keyboard, focus, semantics, labels, contrast, reduced motion, zoom, and screen-reader requirements. Add automated accessibility checks plus a manual checklist.
7. Connect every displayed state to actual API data. Synthetic fixtures may seed the demo but may not bypass the agent/tools/state machine.
8. Add a judge-friendly demo reset/start control that cannot expose secrets or delete non-demo data.
9. Display the ten-case evaluation as a compact evidence page or section with failures included. Do not show an inflated percentage without counts and conditions.
10. Deploy the frontend. Prefer Amplify Hosting; use S3 + CloudFront or Vercel if Amplify blocks progress. Configure the real public API URL and verify a clean-browser journey.

Verification:
- lint, typecheck, frontend tests, production build, backend suite, and evaluation run pass;
- automated accessibility scan has zero serious/critical issues on the hero pages, or every unresolved issue is documented;
- keyboard-only manual pass completes;
- narrow mobile and desktop viewport passes complete;
- clean/incognito browser can run the public hero path without AWS credentials;
- one negative branch reaches Needs your decision;
- recovery time is system-measured;
- commit passing work with message: feat: deliver accessible OpenDoor Relay experience

Create docs/execution/RUN_4_REPORT.md containing: commit SHA, public app URL, page inventory, screenshots to capture, exact tests/results, accessibility evidence, public hero-path result, observed recovery time, known defects, and fallbacks.

RUN 4 STOP CONDITION: Stop after the public multi-page product demonstrates the hero and negative paths, the commit exists, and RUN_4_REPORT.md is written. Do not record the final video or submit to Devpost.
```

### Human acceptance checkpoint

- [ ] A judge understands the problem within 15 seconds.
- [ ] The agent's actions are visible as consequences and evidence, not internal jargon.
- [ ] All six pages exist and share one coherent state.
- [ ] The entire public journey works without account creation.
- [ ] Keyboard and mobile use are credible.
- [ ] Real metric and evaluation results are visible, including failures.

---

# RUN 5 — Release hardening, evidence package, and submission handoff

**Budget:** approximately 5 focused hours  
**Purpose:** freeze scope, prove cold-start reproducibility, and prepare everything needed for the five-minute pitch.

### Paste into Antigravity

```text
Execute RUN 5 from OPENDOOR_RELAY_ANTIGRAVITY_EXECUTION_BOSS.md. Read all prior reports. This is a release and evidence run: fix only submission-critical defects and do not add features. Stop before actually submitting to Devpost.

Release work:
1. Run the complete verification matrix: backend tests, policy tests, frontend tests/build, evaluation, AWS smoke test, public incognito hero path, negative path, accessibility scan, secret scan, and dependency/license review.
2. Perform a cold-start rehearsal using the README in a clean temporary checkout or equivalent clean environment. Correct every missing step without exposing credentials.
3. Finalize README.md with: one-sentence hook; problem and user; hero flow; why it is an agent; Strands/Bedrock/AgentCore usage; deterministic safety; architecture; setup; environment-variable table; local demo; deployed demo; tests/evaluation; limitations; privacy; license; and teardown.
4. Finalize docs/architecture.md and export a clean architecture PNG/SVG if the available tooling can render it accurately. Show browser roles, control API, Strands agent, policy tools, AgentCore or disclosed fallback, DynamoDB, Scheduler, SES, and observability.
5. Create docs/DEMO_SCRIPT.md for a maximum 5-minute recording using the exact sequence below. Include recovery instructions if the live service fails during recording.
6. Create docs/DEVPOST_HANDOFF.md with copy-ready fields: project name, tagline, track, inspiration, what it does, how it was built, challenges, accomplishments, lessons, future work, AWS Builder ID placeholder, public repo, public app, video placeholder, architecture path, license confirmation, and disclosure of pre-existing/generated code.
7. Create docs/EVIDENCE_INDEX.md linking every claim to a test result, trace, screenshot, evaluation artifact, or live page. Remove or soften unsupported claims.
8. Confirm the GitHub repository is ready to be public: no secrets, no personal data, no internal prompts required at runtime, correct license, clear setup, clean root, and successful push. Do not change repository visibility unless the human explicitly approves it.
9. Create docs/RECORDING_CHECKLIST.md with browser cleanup, synthetic data reset, email tabs, zoom, microphone, timer, fallback recording, export resolution, and public-video verification.
10. Freeze code after critical fixes. Commit with message: chore: freeze OpenDoor Relay submission release and push the exact verified commit.

Five-minute demo timeline:
- 0:00-0:25 — Show the confirmed attendee plan and Provider A's decline.
- 0:25-1:10 — Open recovery case; show Strands interpretation, policy-safe matching, and Provider B selection.
- 1:10-2:05 — Provider B accepts through the genuine tokenized response page.
- 2:05-2:50 — Show provider assignment, run of show, room checklist, staff task, and attendee plan updating.
- 2:50-3:30 — Attendee confirms; stop on the measured recovery time.
- 3:30-4:10 — Run over-budget or non-equivalent branch; show Needs your decision.
- 4:10-4:40 — Show ten-case results and one sanitized AgentCore/CloudWatch trace.
- 4:40-5:00 — Show architecture and close: OpenDoor Relay keeps an event accessible when the original plan fails.

Create docs/execution/FINAL_RELEASE_REPORT.md containing: release commit SHA, public app/API/repo URLs, complete check results, observed metric, evaluation summary, AgentCore/SES/fallback status, cold-start result, known limitations, recording readiness, Devpost readiness, and exact remaining human actions. Never include secrets.

RUN 5 STOP CONDITION: Stop when the verified release commit is pushed and all handoff files exist. Do not submit to Devpost, publish a video, change repository visibility, or make claims on the user's behalf without explicit approval.
```

### Final human acceptance checkpoint

- [ ] Public application works in an incognito browser.
- [ ] Public repository contains setup, license, architecture, tests, and honest limitations.
- [ ] Repository setup succeeds from a clean checkout.
- [ ] No secret, diagnosis, personal data, fake receipt, or unsupported metric is present.
- [ ] The video plan fits under five minutes.
- [ ] The final commit SHA matches the code demonstrated and pushed.
- [ ] Devpost handoff contains every required link and field.

---

## 5. Stop-loss and fallback ladder

Use the first level that preserves a genuine end-to-end proof. Record every fallback in the README and final report.

1. **Primary:** AgentCore Runtime + Strands + Bedrock + DynamoDB + Scheduler + SES on AWS.
2. **AgentCore blocked after 60 minutes:** same Strands core through Lambda/container; retain Bedrock, DynamoDB, Scheduler, SES, and observability.
3. **SES sandbox limitation:** verified team inboxes plus the genuine tokenized provider portal. Do not claim arbitrary outbound delivery.
4. **Model-access blocker:** use another currently supported model through the same Strands adapter. Keep AWS state and actions real. Use the rehearsal model only for labeled test/demo fallback.
5. **Amplify delay:** S3 + CloudFront or Vercel frontend with the AWS backend unchanged.
6. **Live outage during recording:** use the deterministic rehearsal model through the same tools, policies, API, and durable state; label it on screen and show previously captured live AWS evidence.

Never spend more than 60 minutes repeatedly fighting one quota, permission, region, or verification gate.

---

## 6. Evidence and honesty rules

- “Live” means the external service actually executed during the captured run.
- “AgentCore” requires a verifiable runtime invocation or trace.
- “Email sent” requires an SES acceptance/result and receipt in a verified inbox.
- “Recovered in N seconds” must come from persisted timestamps.
- “Zero unsafe actions” must be scoped to the named evaluation set.
- A seeded provider directory is acceptable when labeled synthetic; never call it a live marketplace.
- Do not expose chain-of-thought. Show concise decision summaries, tool calls, policy results, and state changes.
- Do not hide failed evaluation cases.
- Do not claim legal compliance, accessibility certification, medical safety, or universal availability.

---

## 7. When to return to ChatGPT for inspection

After each run, bring back only:

1. the corresponding `RUN_n_REPORT.md` or `FINAL_RELEASE_REPORT.md`;
2. the exact error text for any failed acceptance check;
3. screenshots only when the report asks for visual confirmation; and
4. the public URL after Runs 3 or 4.

Do not paste credentials, `.env` contents, access tokens, response tokens, AWS account numbers, or private console URLs.

### If Antigravity stops mid-run

Paste:

```text
Resume the active run only. Read OPENDOOR_RELAY_ANTIGRAVITY_EXECUTION_BOSS.md, git status, the latest completed RUN report, and the current task/output logs. State what is already complete, what is partially changed, and the smallest safe continuation. Preserve all work, do not reset or delete files, do not repeat completed cloud mutations, and stop at the active run's original STOP condition.
```

### If Antigravity starts adding extras

Paste:

```text
Scope correction: stop feature expansion. Re-read the Locked product contract and the active run's acceptance checkpoint. Remove only your uncommitted out-of-scope additions when safe, preserve user work, and complete the smallest end-to-end accessibility recovery proof. No generic dashboard, chat-first UI, diagnosis workflow, marketplace, payments, decorative multi-agent system, or CALL-E integration.
```

---

## 8. Final Definition of Done

OpenDoor Relay is done only when a judge can witness this without trusting narration:

> A confirmed accessibility provider declines. A Strands agent interprets the failure, uses policy-safe tools to select and contact an equivalent backup, receives a genuine response, durably updates every affected operational view, gets attendee confirmation, displays the measured recovery time, and blocks a second unsafe recovery for human decision.

Everything else is secondary.
