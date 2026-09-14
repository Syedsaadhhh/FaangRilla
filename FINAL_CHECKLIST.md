# FINAL CHECKLIST BEFORE SUBMISSION

- [x] **Strands SDK Integration**: Verified load-bearing usage in `orchestrator.py` and `recovery.py`.
- [x] **Privacy Scan**: No AWS credentials, private keys, or personal email values were found in tracked source.
- [x] **README Truth**: README accurately distinguishes deployed rehearsal infrastructure from blocked Bedrock and undeployed AgentCore.
- [x] **Tests Passing**: Fresh verification completed with 46/46 backend tests passing.
- [x] **Frontend Built**: The latest loading-timeout and retry-state changes passed TypeScript and Vite production builds.
- [x] **Architecture Diagram**: Uploadable 1600×900 PNG plus editable SVG/Mermaid sources exist in `docs/assets/`.
- [x] **Demo Package**: Runbook, script, shot list, and final recording master exist.
- [x] **Devpost Draft**: `DEVPOST_SUBMISSION.md` is prepared.
- [x] **AWS Deployment**: The Strands-integrated backend is deployed in `OpenDoorRelayStack`.
- [x] **Live Health Verification**: Vercel `/health` returns `healthy`, `agent_framework=strands-agents`, and `model_mode=deterministic-rehearsal`.
- [x] **AWS-backed Hero Flow**: The public Vercel URL completed failure → provider acceptance → attendee confirmation → timeline, then reset to `CONFIRMED`.
- [x] **Public Repository**: Verified public with MIT license and final source on `main`.
- [x] **Live Frontend**: https://opendoor-relay.vercel.app/ serves the UI and proxies to the AWS API.
- [ ] **Redeploy Latest Retry Fix**: The Vercel project is a manual deployment and is not GitHub-linked. Connect `Syedsaadhhh/FaangRilla`, set Root Directory to `frontend`, and deploy current `main`.
- [ ] **Record Video**: Record the final working demo (maximum 5 minutes).
- [ ] **Upload Video**: Upload publicly/unlisted and verify playback while signed out.
- [ ] **Submit Devpost**: Upload the architecture PNG, add the video/live links and AWS Builder ID, then submit before the deadline.

## Truth Boundary

The deployed backend uses the genuine Strands Agents SDK, but model inference is `deterministic-rehearsal` because Bedrock is quota-blocked. AgentCore is not deployed. SES sender configuration exists, but live email delivery is not claimed. Do not state otherwise in the demo or submission.
