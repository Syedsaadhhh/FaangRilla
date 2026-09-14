# OPEN DOOR RELAY: DEMO SCRIPT

**0:00 - 0:30 (Introduction)**
"Hi, we built OpenDoor Relay. The problem we're solving is catastrophic dropouts in accessibility services. Imagine a sign language interpreter cancels 45 minutes before a conference starts. Organizers scramble, and attendees are excluded. Our judge memory sentence is: OpenDoor Relay keeps an event accessible when the original plan fails."

**0:30 - 1:30 (The Dashboard & Architecture)**
"Here is the OpenDoor Relay dashboard. We have an upcoming 'Community Tech & Accessibility Workshop' with Provider A confirmed for live captioning. Behind the scenes, we use a Python FastAPI backend orchestrated by the Strands Agents SDK. When deployed, it runs serverless on AWS Lambda and API Gateway with DynamoDB for persistence."

**1:30 - 2:30 (The Crisis & Orchestration)**
"Let's trigger a crisis. Provider A drops out due to sudden equipment failure. Immediately, the Strands Agent springs into action. You can see the timeline updating. It evaluates backup providers. It blocks Provider C because they exceed our hard budget ceiling. It selects Provider B, Beacon Live Access, and dispatches a secure offer link."

**2:30 - 3:30 (Provider Resolution)**
"Now we switch to the perspective of Provider B. They receive an email with a secure link. They open this portal and click 'Accept' — indicating they can cover the event. The agent parses this response, ensures it isn't an expired token or a duplicate click, and updates the accommodation plan. Finally, it notifies the attendee."

**3:30 - 4:30 (Verification & Trace)**
"The dashboard now shows the event is RECOVERED and the attendee is confirmed. No humans had to scramble. Look at this developer trace: we can see the exact `MODEL_DECISION` points from the Strands SDK, alongside the deterministic `POLICY_APPROVED` guardrails that kept the agent safely within budget limits."

**4:30 - 5:00 (Conclusion)**
"OpenDoor Relay prevents exclusion through autonomous, safe, and verifiable recovery. Thank you."
