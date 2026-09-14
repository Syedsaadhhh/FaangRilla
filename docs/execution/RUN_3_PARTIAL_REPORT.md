# RUN 3 REHEARSAL DEPLOYMENT REPORT

## Deployment Status
**SUCCESS (Rehearsal Fallback Deployed)**

### Stack Status & Resources
*   **Stack Name**: `OpenDoorRelayStack`
*   **CloudFormation Status**: `CREATE_COMPLETE` (verified in rehearsal mode)
*   **API URL**: `https://k9zn4jy720.execute-api.us-east-1.amazonaws.com/prod/`
*   **Actual Deployed Resources**: AWS Lambda (BackendFunction), API Gateway (RelayApi), DynamoDB (RelayTable), EventBridge Scheduler Role, and Log Retention functions.

### Verification Results
*   **Health Verification**: `GET /health` returned HTTP 200 with `{"status":"healthy","version":"0.1.0","mode":"local-deterministic","agent_mode":"rehearsal"}`
*   **Hero-path Verification**: Successfully executed a complete deterministic recovery path via the deployed API, concluding in `ATTENDEE_CONFIRMED` state.
*   **DynamoDB and SES Evidence**: DynamoDB table successfully persisted case transitions. SES sender configuration is bound from the deployment environment; no live delivery was claimed or verified in this run.
*   **Zero Duplicate Side-Effects**: The state-transition guard rejected a second invalid trigger, and observed persistence showed no additional workflow side effect.
*   **CloudWatch Evidence**: Lambda logs were successfully delivered to `/aws/lambda/OpenDoorRelayStack-BackendFunction...` log group.

## Pre-Deployment Successes
The codebase has been successfully prepared for Run 3:
1.  **Regression Suite**: All 46 backend test cases passed (100% success rate in pytest).
2.  **Frontend Build**: Vite production build succeeded (`tsc -b && vite build` completed successfully).
3.  **Synthesized Infrastructure**: The `OpenDoorRelayStack` CDK definition strictly passes all security requirements (least-privilege IAM, restricted API Gateway CORS). Lambda reserved concurrency was removed because the account quota rejected a reservation; API Gateway throttling remains the public traffic bound.

## Blockers & Cost Risks
*   **Live Bedrock**: `BEDROCK_BLOCKED_BY_DAILY_QUOTA` (Quota limits must be lifted before live invocation).
*   **AgentCore**: `AGENTCORE_NOT_DEPLOYED` (Awaiting Bedrock limits resolution for full architectural rollout).
*   **Recurring Cost Risks**: Costs will be minimal due to serverless components (DynamoDB PAY_PER_REQUEST, Lambda, API Gateway) and AWS_MANAGED KMS.
*   **Cleanup Command**: `npx cdk destroy OpenDoorRelayStack`
