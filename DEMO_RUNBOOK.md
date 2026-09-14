# OPEN DOOR RELAY: DEMO RUNBOOK

**Target Duration**: 5:00
**Mode**: AWS-backed deterministic rehearsal
**Frontend**: Local Vite UI
**Backend**: Live AWS API Gateway + Lambda
**Agent Framework**: Strands Agents SDK
**Model Mode**: Deterministic rehearsal (live Bedrock quota-blocked)

## Pre-flight
1. Pull latest `main`.
2. Start the frontend against the deployed API:

```powershell
Set-Location 'C:\Users\AHSAN\Documents\FaangRilla_Work\frontend'
$env:VITE_API_BASE_URL='https://k9zn4jy720.execute-api.us-east-1.amazonaws.com/prod'
npm run dev
```

3. Open `http://localhost:5173`.
4. Keep DevTools hidden unless a failure occurs.
5. Before recording, verify the AWS backend once:

```powershell
Invoke-RestMethod 'https://k9zn4jy720.execute-api.us-east-1.amazonaws.com/prod/health' | Format-List
```

Expected proof fields include `status=healthy`, `agent_framework=strands-agents`, and `model_mode=deterministic-rehearsal`.

## Demo Walkthrough
1. **Problem State** — Show the Community Tech & Accessibility Workshop with Provider A (Starlight Captioning Co.) confirmed.
2. **Trigger Failure** — Trigger the provider dropout.
3. **Autonomous Recovery** — Show the Strands-driven recovery timeline evaluating replacements.
4. **Guardrail Proof** — Show Provider C blocked for policy/budget reasons and Provider B selected as eligible.
5. **Provider Response** — Open the generated Provider B response flow and accept the offer.
6. **Resolution** — Return to the main view and show recovery reaching `RECOVERED`, then `ATTENDEE_CONFIRMED`.
7. **Evidence** — Show the sanitized developer trace only long enough to point out `MODEL_DECISION` / tool execution / `POLICY_APPROVED` evidence.
8. **Close** — State that the backend is live on AWS while model inference remains deliberately deterministic because Bedrock is quota-blocked.

## Recording Truth Rules
- Say: “The Strands agent orchestration is deployed on AWS.”
- Say: “The model is running in deterministic rehearsal mode for this submission because Bedrock quota is blocked.”
- Do not say Bedrock is live.
- Do not say AgentCore is deployed.
- Do not claim real SES delivery unless separately verified during this session.

## Failure Rule
If the AWS-backed hero flow fails during rehearsal, do not start refactoring infrastructure. Capture the exact failing request/response, fix only the minimum deterministic blocker, re-run the hero path once, then record.
