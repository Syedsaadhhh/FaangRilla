# OPEN DOOR RELAY: DEMO RUNBOOK

**Target Duration**: 5:00
**Mode**: Local Rehearsal (Due to AWS Quota/SSO block)
**Format**: Screen recording with voiceover

## Setup Instructions (Pre-flight)
1. **Reset State**: Clear any existing dynamo state or run the local reset endpoint.
2. **Start Backend**: `uv run uvicorn opendoor_relay.api.app:app --host 127.0.0.1 --port 8000`
3. **Start Frontend**: `npm run dev` in `frontend/`
4. **Browser**: Open `http://localhost:5173`. Keep Network and Console tabs hidden for a clean look.
5. **CLI Window**: Keep a clear terminal window visible to show logs/developer trace if needed.

## Walkthrough Steps
1. **Show the Dashboard**: Display the confirmed event (Community Tech & Accessibility Workshop) with Provider A (Starlight Captioning Co.).
2. **Trigger the Crisis**: Use the frontend "Trigger Crisis" button or API to simulate Provider A dropping out 45 mins before the event.
3. **Observe Orchestration**: Show the frontend timeline updating as the Strands Agent searches for backups, filters out the over-budget Provider C, and selects Provider B (Beacon Live Access).
4. **Provider Response**: Switch to the simulated Provider B portal link (generated in the trace). Click "ACCEPT".
5. **Resolution**: Show the dashboard updating to `RECOVERED` and then `ATTENDEE_CONFIRMED`.
6. **Show Trace Evidence**: Bring up the developer trace JSON to prove the Strands SDK `MODEL_DECISION` and `POLICY_APPROVED` blocks were actively executed.
