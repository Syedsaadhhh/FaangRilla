# OPEN DOOR RELAY: DEMO SCRIPT

**0:00 - 0:25 — Problem**
“OpenDoor Relay keeps an event accessible when the original plan fails. Imagine a live captioning provider cancels shortly before a workshop. The organizer has minutes to recover, and the attendee should not have to absorb that failure.”

**0:25 - 1:05 — What is live**
“This frontend is connected to our deployed AWS backend through API Gateway and Lambda. The recovery loop itself is orchestrated with the Strands Agents SDK, with DynamoDB persisting state. For this hackathon environment, the model runs in deterministic rehearsal mode because live Bedrock quota is blocked.”

**1:05 - 2:05 — Trigger and autonomous recovery**
“Here Provider A is confirmed. I’ll trigger a last-minute dropout. The recovery agent immediately evaluates approved backups against the attendee’s requirements and hard operational policies. Provider C is rejected because it violates the allowed policy boundary, while Provider B is eligible and receives the bounded replacement offer.”

**2:05 - 3:05 — Provider response**
“Now we switch to the provider response flow. Provider B accepts the secure, time-bound offer. The system validates the response, prevents duplicate side effects, updates the accommodation plan, and continues the recovery workflow.”

**3:05 - 4:05 — Human outcome**
“Back on the organizer view, the case reaches RECOVERED and then ATTENDEE_CONFIRMED. The point is not another chatbot. The agent is doing operational recovery work while deterministic policy checks keep unsafe actions outside its control.”

**4:05 - 4:40 — Evidence**
“This trace separates agent decisions from policy-approved execution. We can see the Strands-driven tool path and the guardrails that reject unsafe actions rather than letting the model override them.”

**4:40 - 5:00 — Close**
“OpenDoor Relay is an accessibility continuity agent: deployed on AWS, orchestrated with Strands, and designed to recover the service before the failure becomes the attendee’s problem.”

## Truth Note
Do not state that live Bedrock inference or AgentCore is active. The deployed agent framework is Strands Agents SDK; the model mode is deterministic rehearsal because Bedrock is quota-blocked.
