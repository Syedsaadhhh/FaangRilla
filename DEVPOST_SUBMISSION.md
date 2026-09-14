# DEVPOST SUBMISSION: OpenDoor Relay

## Pitch
OpenDoor Relay keeps an event accessible when the original plan fails.

## Inspiration
Community events strive for inclusivity, but accessibility plans are fragile. If a sign language interpreter or live captioner drops out 45 minutes before a workshop, the organizers scramble and the attendee who relies on them is effectively excluded. We wanted to eliminate this single point of failure using autonomous agents.

## What it does
OpenDoor Relay is an autonomous accessibility continuity engine. When an accessibility provider cancels, the system instantly:
1. Triggers an orchestration loop via the **Strands Agents SDK**.
2. Evaluates backup providers against strict business policies (e.g. budget ceilings, certification requirements).
3. Dispatches a secure, time-bound offer to the best eligible replacement.
4. Classifies their response to handle ambiguous replies natively.
5. Updates the accommodation plan and notifies the attendee.
If no safe option exists, it escalates to humans with a pre-computed list of safe alternatives.

## How we built it
- **Intelligence**: We integrated the **Strands Agents SDK** into our FastAPI backend to orchestrate the recovery sequence. We wrapped the agent with deterministic safety hooks so it can never exceed budget or assign unqualified providers.
- **Backend**: Python 3.12 with FastAPI.
- **Cloud Infrastructure**: AWS CDK (TypeScript) deploying an entirely serverless architecture. We use AWS Lambda for compute, API Gateway for the REST interface, Amazon DynamoDB for idempotent state persistence, and EventBridge Scheduler for handling offer timeouts.
- **Frontend**: React, TypeScript, and Vite.

## Challenges we ran into
- **AWS Limits**: During the sprint, our AWS account hit unexpected Quota limits (e.g. unable to provision Lambda Reserved Concurrency and Bedrock token limits). We adapted by implementing a robust `RehearsalModel` inside our Strands Agent framework. This allowed us to prove the entire deterministic logic flow locally and deploy the core infrastructure to AWS while failing closed securely.
- **Agent Determinism**: It was challenging to ensure an LLM wouldn't hallucinate a budget exception. We solved this by using strict Typed Tools and moving the state machine guardrails outside the LLM's control in `recovery.py`.

## Accomplishments that we're proud of
- Successfully integrating the Strands SDK in a load-bearing way, not just a superficial chatbot.
- Building a full CI/CD-ready AWS serverless stack.
- Passing a 46-test automated suite (100% success) validating edge cases like duplicate token submissions and expired offers.

## What we learned
Building "Agents for Humans" means the agent shouldn't just be smart—it must be safe. By combining autonomous tool execution with deterministic policy boundaries, we learned how to build a system that users can trust with sensitive operational logistics.

## What's next for OpenDoor Relay
- Resolving AWS Quotas to enable the live `BedrockModel`.
- Integrating real Twilio SMS and SES email delivery for provider dispatch and attendee notifications.
- Expanding the provider matching algorithm to consider geolocation and specific technical requirements (e.g. CART vs ASL).
