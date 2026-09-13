# PRE-DEPLOYMENT AUDIT

## 1. REPOSITORY INTEGRITY
**Status: PASS**
*   **Directory**: Executed within `C:\Users\AHSAN\Documents\FaangRilla_Work` containing the exact copied `.git` repository.
*   **Git State**: Branch is `main`, origin is `Syedsaadhhh/FaangRilla`.
*   **Baseline Commits**: `b21eeed` and `d33255a` are present.
*   **Nested Repositories**: None found.
*   **Clean Up**: Accidental preflight artifacts have been removed. Tracked files and `.venv` remain intact.

## 2. CORRECT RUNTIME CLAIMS
**Status: PASS**
*   **Fallback Acknowledgment**: The stack explicitly outputs the description `"Temporary AWS-hosted fallback API while live Bedrock and AgentCore proof remain pending."`
*   **Agent Environment**: `AGENT_MODE=rehearsal` and `AGENTCORE_STATUS=NOT_DEPLOYED` are set.
*   **Bedrock Configuration**: `BEDROCK_MODEL_ID` defaults to `us.amazon.nova-micro-v1:0` if not overridden. Fail-closed behavior is enforced. No silent production fallback is claimed.

## 3. CDK SOURCE AUDIT
**Status: PASS**
*   **Stack Name**: `OpenDoorRelayStack`
*   **DynamoDB**: Configured with `PAY_PER_REQUEST`, `ttl` attribute enabled, and `AWS_MANAGED` encryption.
*   **Lambda Function**: Bounded at 30 seconds timeout, 512 MB memory, and 5 reserved concurrent executions. CloudWatch log retention set to ONE_WEEK. No secrets in environment variables.
*   **API Gateway**: Restricted CORS to `http://localhost:5173` and `http://127.0.0.1:5173`. Throttling enabled (Rate: 10, Burst: 5).
*   **Cost & Footprint**: No persistent high-cost resources (no NAT Gateway, EC2, RDS, OpenSearch). All dependencies pinned. CDK CLI invoked via `npx`. No nested CDK init.

## 4. IAM AUDIT
**Status: PASS**
| Role Name | Trusted Principal | Allowed Actions | Resource Scope |
| :--- | :--- | :--- | :--- |
| **BackendFunction/ServiceRole** | `lambda.amazonaws.com` | `bedrock:InvokeModel`, `bedrock:InvokeModelWithResponseStream` | `arn:aws:bedrock:${Region}::foundation-model/*`, `arn:aws:bedrock:${Region}:${Account}:inference-profile/*` |
| | | `ses:SendEmail`, `ses:SendRawEmail` | `arn:aws:ses:${Region}:${Account}:identity/*` |
| | | `scheduler:CreateSchedule`, `scheduler:DeleteSchedule`, `scheduler:GetSchedule` | `arn:aws:scheduler:${Region}:${Account}:schedule/default/*` |
| | | `iam:PassRole` | Restricted strictly to `SchedulerRole` ARN |
| | | DynamoDB Read/Write | Restricted strictly to `RelayTable` ARN and Indices |
| **SchedulerRole** | `scheduler.amazonaws.com` | `lambda:InvokeFunction` | Restricted strictly to `BackendFunction` ARN |

*(Note: No `AdministratorAccess`, `PowerUserAccess`, `BedrockFullAccess`, etc. No `*` on resources where narrower ARNs apply).*

## 5. BUILD AND SYNTH VALIDATION
**Status: PASS**
All commands exited with successful `0` status codes:
*   `git status` (clean except known untracked artifacts)
*   `git diff --stat` (shows strict backend/infra modifications)
*   `npx tsc --noEmit` (clean typecheck)
*   `npx cdk list`
*   `npx cdk synth --strict` (Synthesized CloudFormation strictly matches expectations)
*   `npx cdk diff`
*   `npx cdk diff --security-only`

## 6. DEPLOYMENT AND CLEANUP PLAN
**Status: PASS**
*   **Exact Stack Name**: `OpenDoorRelayStack`
*   **Estimated Recurring Resources**:
    *   DynamoDB Table (PAY_PER_REQUEST, costs only on I/O operations).
    *   Lambda Function (Serverless, costs only during execution).
    *   API Gateway (Serverless, costs per million requests).
    *   CloudWatch Logs (Costs per GB ingested/stored).
*   **Chargeable While Idle**: Minimal. Storage for DynamoDB and CloudWatch Logs only.
*   **Exact Post-Demo Cleanup Command**: `npx cdk destroy OpenDoorRelayStack`
*   **Preserves CDKToolkit**: Yes. Deleting the application stack will safely leave the CDK bootstrap resources intact.
*   **Expected Stack Outputs**: `ApiUrl` (The base endpoint of the API Gateway proxy).
*   **Rollback Procedure**: AWS CloudFormation will automatically rollback all resources if deployment fails.

## 7. AGENTCORE PLAN (NOT DEPLOYED)
**Status: BLOCKED**
Actual AgentCore Runtime deployment is planned but deferred due to Bedrock quota limits. When authorized, the final deployment MUST include:
*   HTTP protocol communication.
*   An ARM64 container image hosted on ECR.
*   Exposed port `8080` with a `/health` endpoint.
*   A dedicated least-privilege execution role.
*   An authenticated invocation mechanism verifying `READY` status.
*   CloudWatch trace evidence of the actual agent runtime.
*(Note: None of these resources are included in the current fallback CDK stack).*

## 8. BLOCKERS
*   **Live Bedrock**: `BLOCKED_BY_DAILY_QUOTA` (Too many tokens per day throttling).
*   **AgentCore**: Awaiting resolution of the underlying Bedrock quota before final proof-of-execution can proceed.
