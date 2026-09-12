# RUN 1 Report — Foundation and Executable Vertical Slice

**Project:** FaangRilla (Provisional Product Name: OpenDoor Relay)  
**Workspace & Repository:** `FaangRilla`  
**Git Remote:** None configured locally prior to handoff  
**Run:** RUN 1  
**Status:** PASSED  
**Commit Message:** `feat: establish OpenDoor Relay vertical slice`  
**Verified Run 1 build commit:** `857fd375a661796a2cd3c70fbbe388368fa5f1c8`  

---

## 1. Alignment Corrections Implemented

1. **Repository & Workspace Naming:**
   - Folder name and GitHub repository name remain `FaangRilla`.
   - Checked `git remote -v`: no remote was configured prior to handoff. Preserved exact local state without guessing a remote URL.
2. **Centralized Brand Configuration:**
   - Centralized visible display name in [`frontend/src/config/brand.ts`](../../frontend/src/config/brand.ts) (`BRAND_CONFIG`).
   - Flagged name as provisional (`isProvisional: true`) so the public brand can be safely swapped before Run 4 without code churn.
   - Preserved internal Python package name `opendoor_relay` for structural stability.
3. **Dynamic Budget Ceiling Policy:**
   - Confirmed deterministic policy strictly evaluates `plan.budget_ceiling` dynamically from the input `AccommodationPlan`.
   - Verified via unit test `test_budget_dynamic_ceiling_from_plan` that varying the ceiling dynamically allows ($500 ceiling) or blocks ($200 ceiling) providers without any hardcoded $300 constant.
4. **Official Headline Metric vs. Supporting Metric:**
   - **Headline Metric:** `time_to_confirmed_seconds` (`confirmed_at - opened_at`): Time from original provider failure to final attendee confirmation.
   - **Supporting Internal Metric:** `time_to_recovered_seconds` (`recovered_at - opened_at`): Time from failure to backup provider acceptance.
   - Displayed and labeled prominently in [`RecoveryCasePage.tsx`](../../frontend/src/pages/RecoveryCasePage.tsx) and verified via API responses.
5. **Evaluation Endpoint State:**
   - `GET /api/evaluation/latest` returns an explicit typed `EvaluationStatusResponse` with `status: "NOT_GENERATED"`, `run: "RUN_1"`, and `results: null`.
   - Zero evaluation results fabricated; the full 10-case evaluation suite is scheduled for Run 2.

---

## 2. Changed-File Summary

- **Repository Root:**
  - `LICENSE`: MIT License
  - `.gitignore`: Ignoring `.venv`, `node_modules`, `dist`, `.env*`
  - `.editorconfig`: Format settings (2 spaces frontend, 4 spaces Python)
  - `SECURITY.md`: Data minimization and strict privacy boundaries (functional access needs only; no medical diagnoses)
  - `.env.example`: Non-secret placeholders only
  - `README.md`: Architecture overview and exact local commands
- **Backend (`backend/`):**
  - `pyproject.toml` & `backend/requirements.lock`: Python 3.12 FastAPI backend package with pinned dependencies
  - `backend/README.md`: Backend documentation
  - `src/opendoor_relay/domain/models.py`: Typed Pydantic models for Event, AccommodationPlan, Provider, RecoveryCase, ProviderOffer, and AuditEvent
  - `src/opendoor_relay/domain/state_machine.py`: Deterministic recovery state machine transition graph and guard validation
  - `src/opendoor_relay/domain/policy.py`: Equivalence, dynamic budget ceiling (`plan.budget_ceiling`), and privacy consent filtering
  - `src/opendoor_relay/repository/interface.py`: Authoritative persistence interface
  - `src/opendoor_relay/repository/memory.py`: Thread-safe in-memory store with synthetic demo fixtures
  - `src/opendoor_relay/provider_gateway/interface.py`: Outbound provider gateway interface
  - `src/opendoor_relay/provider_gateway/local_inbox.py`: Real single-use expiring tokens (SHA-256 hashed) and local response portal URLs
  - `src/opendoor_relay/service/recovery.py`: Deterministic recovery orchestrator with idempotency and transition enforcement
  - `src/opendoor_relay/api/schemas.py`: Pydantic request/response schemas with headline metric and typed `EvaluationStatusResponse`
  - `src/opendoor_relay/api/routes.py`: REST endpoints (`/health`, `/api/demo/event`, `/api/cases/*`, `/api/provider/*`, `/api/evaluation/latest`)
  - `src/opendoor_relay/api/app.py`: FastAPI app factory and CORS middleware
  - `tests/test_state_machine.py`: State transition graph & invalid transition rejection tests (2 tests)
  - `tests/test_policy.py`: Equivalence, dynamic budget ceiling, and consent privacy tests (13 tests)
  - `tests/test_tokens_and_expiry.py`: Secure token generation, SHA-256 hashing, and expiration handling tests (3 tests)
  - `tests/test_idempotency.py`: Replayed provider response idempotency tests (1 test)
  - `tests/test_hero_recovery.py`: End-to-end integration test of the full hero recovery loop and NOT_GENERATED evaluation check (3 tests)
- **Frontend (`frontend/`):**
  - `package.json` & `package-lock.json`: React 18 + TypeScript + Vite configuration
  - `tsconfig.json`, `tsconfig.node.json`, `vite.config.ts`, `index.html`
  - `src/config/brand.ts`: Centralized provisional brand configuration
  - `src/index.css`: Accessible design system tokens
  - `src/types.ts`: TypeScript contracts matching backend models
  - `src/api.ts`: Typed fetch client for backend endpoints
  - `src/pages/EventPage.tsx`: Event accessibility commitments and failure trigger control
  - `src/pages/AttendeePlanPage.tsx`: Personal accommodation plan, consent notice, and attendee confirmation action
  - `src/pages/ProviderResponsePage.tsx`: Mobile-friendly tokenized accept/decline portal
  - `src/pages/RecoveryCasePage.tsx`: Visual hero recovery case timeline with headline (`confirmed_at - opened_at`) and supporting metrics
  - `src/App.tsx` & `src/main.tsx`: Root navigation and state management
- **Infrastructure (`infra/`):**
  - `package.json`: CDK TypeScript package definition
  - `cdk_placeholder.ts`: Architecture mapping for DynamoDB, Lambda, Bedrock/AgentCore, Scheduler, and SES in Run 3
- **Automation Scripts (`scripts/`):**
  - `run-local.ps1` & `run-local.sh`: Start backend and frontend concurrently
  - `verify-run-1.ps1` & `verify-run-1.sh`: Automated 9-step hero path and evaluation state verification script

---

## 3. Exact Commands and Results

1. **Virtual Environment & Dependencies:**
   ```powershell
   uv venv backend/.venv --python 3.12
   uv pip install -e "backend/[test]" --python backend/.venv/Scripts/python.exe
   uv pip compile backend/pyproject.toml --extra test -o backend/requirements.lock
   ```
   *Result:* Exit code 0. Installed 29 packages with exact reproducible lockfile.

2. **Backend Unit Tests:**
   ```powershell
   backend/.venv/Scripts/python.exe -m pytest backend/tests -v
   ```
   *Result:* Exit code 0. **22 passed, 0 failed** in 8.72s.

3. **Frontend Dependencies & Production Build:**
   ```powershell
   npm install --prefix frontend
   npm --prefix frontend run build
   ```
   *Result:* Exit code 0. TypeScript check passed; Vite built production bundle in 14.84s with 0 errors.

4. **Hero Path End-to-End Automated Verification (9 Steps):**
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts/verify-run-1.ps1
   ```
   *Result:* Exit code 0.
   - `[1/9]` GET `/health` &rarr; `healthy`
   - `[2/9]` POST `/api/demo/reset` & GET `/api/demo/event` &rarr; Initial state CONFIRMED, Provider A assigned
   - `[3/9]` POST `/api/cases/case-synthetic-001/provider-failure` &rarr; Case REPLACEMENT_PENDING, Provider B selected (Provider C blocked by dynamic budget ceiling)
   - `[4/9]` GET `/api/provider/offer/{token}` &rarr; Verified token loads Beacon Live Access offer
   - `[5/9]` POST `/api/provider/respond/{token}` (ACCEPT) &rarr; Offer ACCEPTED, Case ATTENDEE_CONFIRMATION_PENDING
   - `[6/9]` Duplicate response replay &rarr; **Idempotent: 0 duplicate audit events, 0 version increments**
   - `[7/9]` POST `/api/cases/case-synthetic-001/attendee-confirm` &rarr; State ATTENDEE_CONFIRMED, recovery clock locked
   - `[8/9]` Timeline & Metrics &rarr; Verified 6 audit events; Headline Metric: **0.93s**, Supporting Metric: **0.65s**
   - `[9/9]` GET `/api/evaluation/latest` &rarr; Verified explicit typed state `NOT_GENERATED` (`run="RUN_1"`, `results=null`)

   > **Note on Observed Timing:** The 0.93-second headline result observed during Run 1 came directly from the automated local verification script (`verify-run-1.ps1` against local in-memory storage) and is not the final judge-facing live recovery metric. The official live metric will be measured and recorded during deployed runs with real network/cloud interactions.

---

## 4. Test Counts & Verification Metrics

- **Backend Unit Tests:** 22 passed / 22 total (100%)
  - State machine valid/invalid transitions: 2
  - Deterministic policy (equivalence, dynamic budget ceiling, consent scope, prohibited diagnosis): 13
  - Expiring token generation, SHA-256 hashing, expiration, and invalid token rejection: 3
  - Replay idempotency: 1
  - Hero integration, blocked Provider C, and NOT_GENERATED evaluation check: 3
- **Frontend Build:** TypeScript check passed, production bundle clean (separate lint check not configured in Run 1)
- **Verification Script:** 9/9 assertions passed, exit code 0
- **Duplicate Side Effects:** Exactly 0
- **Unsafe Executed Actions:** Exactly 0

---

## 5. Local URLs

- **Frontend Application:** `http://localhost:5173`
- **Backend API Base:** `http://127.0.0.1:8000`
- **API Health Check:** `http://127.0.0.1:8000/health`
- **Interactive OpenAPI Docs:** `http://127.0.0.1:8000/docs`
- **Evaluation Status:** `http://127.0.0.1:8000/api/evaluation/latest`
- **Provider Token Portal:** `http://localhost:5173/provider/respond/{token}`

---

## 6. Unresolved Blockers & Intentional Substitutions

### Blockers
- None for Run 1.
- *Notice for Run 3:* The host environment does not currently have `aws` CLI installed in `PATH`. This must be configured before Run 3 cloud deployment.

### Intentional Substitutions for Run 1
- **Storage:** In-memory repository (`InMemoryRepository`) used in place of DynamoDB. Kept behind `RepositoryInterface` for drop-in DynamoDB support in Run 3.
- **Provider Communication:** `LocalInboxProviderGateway` generating cryptographically secure SHA-256 tokens and local URLs in place of Amazon SES emails.
- **Agent Intelligence:** Deterministic Python policy matching in place of live Strands/Bedrock LLM orchestration (scheduled for Run 2).

---

## 7. Next-Run Risks (Run 2)

1. **Strands Agents SDK Compatibility:** Verifying compatible package versions and dependencies on Python 3.12 for Strands Agents SDK.
2. **Deterministic Rehearsal Model vs. Live Bedrock:** Ensuring the rehearsal model accurately reflects tool calls and safety hook enforcement so tests run deterministically without live AWS credentials, while preparing clean adapters for live Bedrock.
3. **Ten-Case Synthetic Evaluation Suite:** Implementing and running the 10-case evaluation matrix (decline, timeout, ambiguous response, equipment mismatch, language mismatch, duplicate response, over-budget, consent expansion, no equivalent provider, and successful recovery) to transition `/api/evaluation/latest` from `NOT_GENERATED` to populated results.
