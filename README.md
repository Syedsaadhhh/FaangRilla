# OpenDoor Relay

> **Judge memory sentence:** OpenDoor Relay keeps an event accessible when the original plan fails.

OpenDoor Relay is an autonomous accessibility continuity engine built for community events. When a confirmed accessibility provider (e.g. live captioner or sign language interpreter) drops out shortly before an event cutoff, OpenDoor Relay rapidly and deterministically orchestrates an approved replacement, coordinates attendee confirmation, updates all operational views, and measures the exact time to recovery.

---

## Architecture Overview

- **Frontend:** React + TypeScript + Vite (`frontend/`)
- **Backend:** Python 3.12 FastAPI (`backend/`)
- **Intelligence & Orchestration:** Strands Agents SDK + Amazon Bedrock (Run 2)
- **Persistence & Cloud:** In-memory repository (Run 1) -> DynamoDB + EventBridge Scheduler + Amazon SES on AWS (Run 3)
- **Infrastructure as Code:** AWS CDK in TypeScript (`infra/`)

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
Or on Linux/macOS:
```bash
uv venv backend/.venv --python 3.12
source backend/.venv/bin/activate
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
Or on Linux/macOS:
```bash
backend/.venv/bin/python -m uvicorn opendoor_relay.api.app:app --host 127.0.0.1 --port 8000 --reload
```

### Start Frontend (Port 5173)
```bash
cd frontend
npm run dev
```

### Or Run Both Together
Using the provided local runner:
- **Windows:** `powershell -ExecutionPolicy Bypass -File scripts/run-local.ps1`
- **Linux/macOS:** `./scripts/run-local.sh`

---

## Running Tests & Verification

### Run Backend Unit Tests
```powershell
backend/.venv/Scripts/python -m pytest backend/tests -v
```

### Run Frontend Build & Typecheck
```bash
cd frontend
npm run build
cd ..
```

### Run Automated Hero Path Verification (Run 1)
- **Windows:** `powershell -ExecutionPolicy Bypass -File scripts/verify-run-1.ps1`
- **Linux/macOS:** `./scripts/verify-run-1.sh`

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
