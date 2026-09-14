# FINAL CHECKLIST BEFORE SUBMISSION

- [x] **Strands SDK Integration**: Verified load-bearing usage in `orchestrator.py` and `recovery.py`.
- [x] **Privacy Scan**: Verified no AWS credentials, private keys, or personal emails are committed.
- [x] **README Truth**: Updated README to accurately reflect rehearsal mode, AWS infrastructure, and Strands usage.
- [x] **Tests Passing**: 46/46 pytest backend tests passing (100%).
- [x] **Frontend Built**: `npm run build` completed successfully with `VITE_API_BASE_URL` support.
- [x] **Architecture Diagram**: Mermaid syntax repaired in `docs/assets/opendoor-relay-architecture.mmd`.
- [x] **Demo Package**: Runbook, Script, and Shot List exist for the video recording.
- [x] **Devpost Draft**: `DEVPOST_SUBMISSION.md` prepared.
- [x] **AWS Deployment**: Final Strands-integrated backend deployed successfully to `OpenDoorRelayStack`.
- [x] **Live Health Verification**: `/health` returned `healthy`, `agent_framework=strands-agents`, and `model_mode=deterministic-rehearsal`.
- [x] **Final GitHub Push**: Final code and deployment evidence are on `main`.
- [ ] **AWS-backed Hero Flow Check**: Run the frontend against the deployed API and complete one clean recovery path before recording.
- [ ] **Record Video**: Record the final demo (max 5 minutes).
- [ ] **Upload Video**: Upload to YouTube/Vimeo and link to Devpost.
- [ ] **Submit Devpost**: Click the final "Submit" button before 00:00:00 UTC on September 15, 2026.

## Truth Boundary
The deployed backend uses the genuine Strands Agents SDK, but model inference is still `deterministic-rehearsal` because Bedrock is quota-blocked. `AgentCore` is not deployed. Do not claim otherwise in the demo or submission.
