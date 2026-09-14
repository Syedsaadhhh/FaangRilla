# OpenDoor Relay

> **Judge memory sentence:** OpenDoor Relay keeps an event accessible when the original plan fails.

## The Problem
When a confirmed accessibility provider (e.g. live captioner or sign language interpreter) drops out shortly before an event cutoff, event organizers are left scrambling. OpenDoor Relay rapidly and deterministically orchestrates an approved replacement, coordinates attendee confirmation, updates all operational views, and measures the exact time to recovery. It fails closed to prevent assigning out-of-budget or unqualified providers.

## Strands Agents Integration
The core of OpenDoor Relay's recovery capability is built using the **Strands Agents SDK**. The autonomous recovery loop:
1. Orchestrates the recovery sequence utilizing a suite of real tools (`find_eligible_replacements`, `create_provider_offer`, `send_provider_offer`, etc.).
2. Classifies ambiguous or incomplete provider responses to prevent silent failures.
3. Automatically escalates to a human event organizer with safe, pre-computed alternatives if no budget-compliant backup is available or if responses time out.
4. Leaves a transparent, sanitized developer trace distinguishing `MODEL_DECISION` from `POLICY_APPROVED` actions.

## AWS Architecture
The production architecture utilizes a robust serverless stack defined entirely via AWS CDK (`infra/`):
- **API Gateway (RelayApi):** Exposes strictly validated REST endpoints.
- **AWS Lambda (BackendFunction):** Runs the Python 3.12 FastAPI backend + Strands orchestration.
- **Amazon DynamoDB (RelayTable):** Provides robust state persistence with strict idempotency keys.
- **Amazon EventBridge Scheduler:** Manages bounded execution windows for offer timeouts.
- **Amazon SES:** Handles safe email delivery for attendee notifications.

*(Note: In the current deployed environment, reserved concurrency and live Bedrock inference have been removed or downgraded to rehearsal mode due to hackathon-time AWS account quota constraints. The Lambda runs without concurrency locks, and API Gateway acts as the throttling boundary.)*

## Rehearsal Limits
To navigate AWS Bedrock access limits during the hackathon sprint, the deployment currently operates in **Deterministic Rehearsal Mode**.
- `AGENT_MODE=rehearsal`
- `AGENTCORE_STATUS=NOT_DEPLOYED`
The orchestration loop exercises the genuine Strands Agent framework, but the underlying LLM is stubbed with a deterministic local model (`RehearsalModel`) that safely navigates the predefined test fixtures without needing live Bedrock tokens. This ensures the architecture and business logic can be fully evaluated.

---

## Demo & Submission

For the final recording flow, exact click path, side-by-side screen/voice script, hooks, Q&A, and editing rhythm, use:

- [`FINAL_DEMO_RECORDING_MASTER.md`](FINAL_DEMO_RECORDING_MASTER.md)
- [`DEMO_RUNBOOK.md`](DEMO_RUNBOOK.md)
- [`DEVPOST_SUBMISSION.md`](DEVPOST_SUBMISSION.md)

---

## Local Setup & Quickstart

### Prerequisites
- **Node.js:** v20+ (v24 tested) and `npm`
- **Python:** 3.12 managed via `uv` or Python 3.12+
- **Git**

### 1. Backend Setup
From the repository root:
```powershell
# Create Python 3.12 virtual environment using uv
uv venv backend/.venv --python 3.12

# Install backend dependencies
uv pip install -e backend/
```

### 2. Frontend Setup
```bash
cd frontend
npm install
cd ..
```

---

## Running Locally

### Start Backend (Port 8000)
```powershell
backend/.venv/Scripts/python -m uvicorn opendoor_relay.api.app:app --host 127.0.0.1 --port 8000 --reload
```

### Start Frontend (Port 5173)
```bash
cd frontend
npm run dev
```

---

## Synthetic Demo Fixtures

In compliance with the product contract:
- **Workshop:** Community Tech & Accessibility Workshop (synthetic)
- **Attendee Plan:** Live captioning (CART) & front-row seating for Attendee Taylor
- **Provider A:** Starlight Captioning Co. (Initial provider who declines)
- **Provider B:** Beacon Live Access (Eligible approved backup provider)
- **Provider C:** Apex Specialized Services (Blocked: exceeds $300 budget ceiling)

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
