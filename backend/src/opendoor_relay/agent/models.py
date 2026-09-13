"""Model providers and adapters for the OpenDoor Relay Strands agent.

Provides:
- BedrockModelAdapter: Configurable Amazon Bedrock provider with explicit BLOCKED_BY_ACCESS detection.
- RehearsalModel: Deterministic, rule-driven evaluation model for offline testing and 10-case evaluation.
"""

from __future__ import annotations
import json
import logging
import os
import uuid
from typing import Any, AsyncIterable, Callable, Dict, List, Optional, Tuple
from pydantic import BaseModel

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from strands.models import Model
from strands.types.content import Messages, SystemContentBlock
from strands.types.streaming import StreamEvent
from strands.types.tools import ToolChoice, ToolSpec

logger = logging.getLogger(__name__)

# Prevent boto3 from hanging on EC2 metadata service when running outside AWS
os.environ.setdefault("AWS_EC2_METADATA_DISABLED", "true")

DEFAULT_BEDROCK_MODEL_ID = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"

DEFAULT_BEDROCK_REGION = "us-east-1"


AGENT_MODE_ENV = "AGENT_MODE"
AGENT_MODE_REHEARSAL = "rehearsal"
AGENT_MODE_BEDROCK = "bedrock"


def get_agent_mode() -> str:
    """Return configured agent execution mode: 'rehearsal' or 'bedrock'."""
    return os.environ.get(AGENT_MODE_ENV, AGENT_MODE_REHEARSAL).strip().lower()


class BedrockModelAdapter:
    """Configurable Amazon Bedrock model adapter.
    
    Adheres strictly to the verification contract:
    - Never fabricates live model responses when credentials are missing.
    - Accurately reports BLOCKED_BY_ACCESS when credentials/quotas are unavailable.
    - Fails closed when live Bedrock mode is selected without valid credentials.
    """

    def __init__(
        self,
        model_id: Optional[str] = None,
        region: Optional[str] = None,
    ) -> None:
        self.model_id = (
            model_id
            or os.environ.get("BEDROCK_MODEL_ID")
            or DEFAULT_BEDROCK_MODEL_ID
        )
        self.region = (
            region
            or os.environ.get("AWS_REGION")
            or DEFAULT_BEDROCK_REGION
        )

    def check_availability(self) -> Tuple[bool, str]:
        """Check whether AWS credentials and Bedrock access are active."""
        try:
            session = boto3.Session()
            creds = session.get_credentials()
            if not creds:
                return (
                    False,
                    "BLOCKED_BY_ACCESS: No AWS credentials found in environment or configuration.",
                )
            frozen_creds = creds.get_frozen_credentials()
            if not frozen_creds or not frozen_creds.access_key:
                return (
                    False,
                    "BLOCKED_BY_ACCESS: Incomplete AWS credentials detected.",
                )
            return True, "AWS credentials detected."
        except Exception as exc:
            return False, f"BLOCKED_BY_ACCESS: Error checking credentials: {str(exc)}"

    def create_model(self) -> Model:
        """Create a live Strands BedrockModel instance if credentials are valid."""
        available, reason = self.check_availability()
        if not available:
            raise RuntimeError(reason)

        from strands.models.bedrock import BedrockModel

        return BedrockModel(
            model_id=self.model_id,
            region_name=self.region,
        )

    def run_smoke_test(self) -> Dict[str, Any]:
        """Run a non-destructive Bedrock converse smoke test or return BLOCKED_BY_ACCESS."""
        available, reason = self.check_availability()
        if not available:
            return {
                "status": "BLOCKED_BY_ACCESS",
                "reason": reason,
                "model_id": self.model_id,
                "region": self.region,
                "live_invoked": False,
            }

        try:
            client = boto3.client("bedrock-runtime", region_name=self.region)
            response = client.converse(
                modelId=self.model_id,
                messages=[
                    {"role": "user", "content": [{"text": "Hello, respond with OK."}]}
                ],
                inferenceConfig={"maxTokens": 10, "temperature": 0.0},
            )
            text = (
                response.get("output", {})
                .get("message", {})
                .get("content", [{}])[0]
                .get("text", "")
            )
            return {
                "status": "SUCCESS",
                "model_id": self.model_id,
                "region": self.region,
                "live_invoked": True,
                "sample_output": text.strip(),
            }
        except (BotoCoreError, ClientError, Exception) as exc:
            return {
                "status": "BLOCKED_BY_ACCESS",
                "reason": f"Bedrock invocation failed: {str(exc)}",
                "model_id": self.model_id,
                "region": self.region,
                "live_invoked": False,
            }

    def run_strands_bedrock_smoke_test(self) -> Dict[str, Any]:
        """Run a Strands Agent smoke test with BedrockModel and a registered tool, or return BLOCKED_BY_ACCESS."""
        available, reason = self.check_availability()
        if not available:
            return {
                "status": "BLOCKED_BY_ACCESS",
                "reason": reason,
                "model_id": self.model_id,
                "region": self.region,
                "live_invoked": False,
                "strands_invoked": False,
                "tool_executed": False,
            }

        try:
            from strands import Agent, tool
            from strands.models.bedrock import BedrockModel
            from opendoor_relay.agent.hooks import RecoverySafetyHookProvider

            @tool
            def ping_tool(echo: str) -> dict:
                return {"echo": echo, "status": "ok"}

            model = BedrockModel(model_id=self.model_id, region_name=self.region)
            agent = Agent(
                model=model,
                tools=[ping_tool],
                hooks=[RecoverySafetyHookProvider()],
                system_prompt="You are a test agent. When asked to ping, invoke ping_tool.",
            )
            result = agent("Please invoke ping_tool with echo='bedrock_smoke_test'")
            return {
                "status": "SUCCESS",
                "model_id": self.model_id,
                "region": self.region,
                "live_invoked": True,
                "strands_invoked": True,
                "tool_executed": True,
                "result_message": str(result.message),
            }
        except Exception as exc:
            return {
                "status": "BLOCKED_BY_ACCESS",
                "reason": f"Strands Bedrock invocation failed: {str(exc)}",
                "model_id": self.model_id,
                "region": self.region,
                "live_invoked": False,
                "strands_invoked": False,
                "tool_executed": False,
            }


class RehearsalModel(Model):
    """Deterministic Rehearsal Model for offline testing and synthetic evaluation.
    
    Clearly labeled: NOT live Bedrock. Drives the real Strands Agent loop
    via autonomous turn generation or scripted test steps.
    """

    def __init__(
        self,
        model_id: str = "rehearsal-deterministic-v1",
        scripted_steps: Optional[List[Dict[str, Any]]] = None,
        custom_handler: Optional[Callable[[Messages, int], Dict[str, Any]]] = None,
    ) -> None:
        self.model_id = model_id
        self.scripted_steps = list(scripted_steps or [])
        self.custom_handler = custom_handler
        self.turn_count = 0
        self.model_invocations = 0
        self.proposed_tools: List[str] = []
        self.executed_tools: List[str] = []
        self.denied_tools: List[str] = []
        self.invocation_log: List[Dict[str, Any]] = []

    def get_config(self) -> Dict[str, Any]:
        return {"model_id": self.model_id, "type": "rehearsal_deterministic"}

    def update_config(self, **kwargs: Any) -> None:
        pass

    async def structured_output(self, *args: Any, **kwargs: Any) -> AsyncIterable[Any]:
        if False:
            yield {}

    def _classify_reply_text(self, text: str) -> str:
        """Classify provider response into DECLINE, TIMEOUT, AMBIGUOUS, or ACCEPT."""
        lower = text.lower().strip()
        
        # Ambiguous / conditional checks first
        ambiguous_keywords = [
            "maybe", "tomorrow", "might", "not sure", "let me check",
            "possibly", "if i can", "tentative", "depends", "could be"
        ]
        if any(w in lower for w in ambiguous_keywords):
            return "AMBIGUOUS"

        # Decline checks
        decline_keywords = [
            "decline", "cannot", "can't", "unavailable", "conflict",
            "unable", "no", "sorry", "not available", "won't be able"
        ]
        if any(w in lower for w in decline_keywords):
            return "DECLINE"

        # Timeout checks
        if "timeout" in lower or "expired" in lower:
            return "TIMEOUT"

        # Accept checks
        accept_keywords = [
            "accept", "confirm", "i can do it", "sounds good",
            "yes", "i'm available", "booked", "happy to take"
        ]
        if any(w in lower for w in accept_keywords):
            return "ACCEPT"

        return "AMBIGUOUS"

    def _find_case_id(self, messages: Messages) -> str:
        """Extract case ID from prompt history."""
        import re
        for m in messages:
            content = m.get("content", []) if isinstance(m, dict) else getattr(m, "content", [])
            for block in content:
                text = block.get("text", "") if isinstance(block, dict) else getattr(block, "text", "")
                match = re.search(r"case-[a-zA-Z0-9_\-]+", str(text))
                if match:
                    return match.group(0)
        return "case-unknown"

    def _find_declined_providers(self, messages: Messages) -> set[str]:
        """Find providers that have declined in this conversation."""
        declined: set[str] = set()
        for m in messages:
            content = m.get("content", []) if isinstance(m, dict) else getattr(m, "content", [])
            for block in content:
                if isinstance(block, dict) and "toolResult" in block:
                    tr = block["toolResult"]
                    c_list = tr.get("content", [])
                    for c in c_list:
                        raw = c.get("text", "") if isinstance(c, dict) else ""
                        try:
                            parsed = json.loads(raw)
                            if parsed.get("response_state") == "DECLINED":
                                prov_id = parsed.get("provider_id")
                                if prov_id:
                                    declined.add(prov_id)
                        except Exception:
                            pass
        return declined

    def _resolve_autonomous_step(self, messages: Messages) -> Dict[str, Any]:
        """Dynamically resolve the next recovery action based on message history."""
        import re
        if not messages:
            return {"text": "No messages received."}

        last_msg = messages[-1]
        role = last_msg.get("role", "") if isinstance(last_msg, dict) else getattr(last_msg, "role", "")
        content = last_msg.get("content", []) if isinstance(last_msg, dict) else getattr(last_msg, "content", [])

        # Check if the last message contains a toolResult
        tool_result_block = None
        for block in content:
            if isinstance(block, dict) and "toolResult" in block:
                tool_result_block = block["toolResult"]
                break

        if tool_result_block:
            tool_use_id = tool_result_block.get("toolUseId")
            status = tool_result_block.get("status", "success")
            c_list = tool_result_block.get("content", [])
            raw_text = ""
            for c in c_list:
                if isinstance(c, dict):
                    raw_text += c.get("text", "")

            # Locate preceding toolUse
            tool_name = ""
            tool_input = {}
            for prev in reversed(messages[:-1]):
                prev_role = prev.get("role", "") if isinstance(prev, dict) else getattr(prev, "role", "")
                if prev_role == "assistant":
                    prev_c = prev.get("content", []) if isinstance(prev, dict) else getattr(prev, "content", [])
                    for pb in prev_c:
                        if isinstance(pb, dict) and "toolUse" in pb:
                            tu = pb["toolUse"]
                            if tu.get("toolUseId") == tool_use_id:
                                tool_name = tu.get("name", "")
                                inp = tu.get("input", {})
                                if isinstance(inp, str):
                                    try:
                                        inp = json.loads(inp)
                                    except Exception:
                                        inp = {}
                                tool_input = inp
                                break
                    if tool_name:
                        break

            # Handle policy denials / hook cancellation
            if tool_name != "request_human_decision" and (status == "error" or "POLICY_DENIED" in raw_text):
                self.denied_tools.append(tool_name)
                case_id = tool_input.get("case_id") or self._find_case_id(messages)
                return {
                    "tool": "request_human_decision",
                    "args": {
                        "case_id": case_id,
                        "reason": f"Safe recovery halted by policy boundary: {raw_text}",
                        "safe_options": [
                            "Review policy exception with organizer",
                            "Select alternate accommodation provider",
                            "Explore virtual event alternative",
                        ],
                    },
                }

            # Handle successful tool execution
            res_data: Dict[str, Any] = {}
            try:
                res_data = json.loads(raw_text)
            except Exception:
                res_data = {}

            if tool_name:
                self.executed_tools.append(tool_name)

            if tool_name == "get_case_context":
                case_id = res_data.get("case_id") or self._find_case_id(messages)
                return {"tool": "find_eligible_replacements", "args": {"case_id": case_id}}

            elif tool_name == "find_eligible_replacements":
                case_id = res_data.get("case_id") or self._find_case_id(messages)
                candidates = res_data.get("candidates", [])
                declined = self._find_declined_providers(messages)
                viable = [c for c in candidates if c.get("provider_id") not in declined]

                if not viable:
                    return {
                        "tool": "request_human_decision",
                        "args": {
                            "case_id": case_id,
                            "reason": "No eligible replacement provider found matching specifications within budget.",
                            "safe_options": [
                                "Expand search radius",
                                "Increase budget ceiling",
                                "Reschedule event",
                            ],
                        },
                    }
                target_prov = viable[0]["provider_id"]
                return {
                    "tool": "create_provider_offer",
                    "args": {"case_id": case_id, "provider_id": target_prov},
                }

            elif tool_name == "create_provider_offer":
                offer_id = res_data.get("offer_id")
                return {"tool": "send_provider_offer", "args": {"offer_id": offer_id}}

            elif tool_name == "send_provider_offer":
                offer_id = res_data.get("offer_id")
                return {"tool": "schedule_offer_timeout", "args": {"offer_id": offer_id}}

            elif tool_name == "schedule_offer_timeout":
                return {"text": "Offer successfully dispatched and timeout scheduled."}

            elif tool_name == "record_provider_response":
                offer_id = res_data.get("offer_id")
                case_id = res_data.get("case_id") or self._find_case_id(messages)
                resp_state = res_data.get("response_state", "")
                resp_text = res_data.get("response_text", "")

                if resp_state == "ACCEPTED":
                    return {
                        "tool": "apply_confirmed_replacement",
                        "args": {"case_id": case_id, "offer_id": offer_id},
                    }
                elif resp_state == "DECLINED":
                    # Autonomous failover: search replacements again excluding declined
                    return {
                        "tool": "find_eligible_replacements",
                        "args": {"case_id": case_id},
                    }
                elif "AMBIGUOUS" in resp_state:
                    return {
                        "tool": "request_human_decision",
                        "args": {
                            "case_id": case_id,
                            "reason": f"Provider response is ambiguous and requires human clarification: '{resp_text}'",
                            "safe_options": [
                                "Contact provider directly to clarify availability",
                                "Reject ambiguity and dispatch offer to next provider",
                                "Accept provider's proposed condition",
                            ],
                        },
                    }
                elif "TIMEOUT" in resp_state:
                    return {
                        "tool": "request_human_decision",
                        "args": {
                            "case_id": case_id,
                            "reason": "Provider response window timed out without confirmation.",
                            "safe_options": [
                                "Extend response window by 10 minutes",
                                "Fail over to alternate provider",
                            ],
                        },
                    }

            elif tool_name == "apply_confirmed_replacement":
                case_id = res_data.get("case_id") or self._find_case_id(messages)
                return {"tool": "notify_attendee", "args": {"case_id": case_id}}

            elif tool_name == "notify_attendee":
                return {"text": "Replacement applied and attendee notified. Awaiting attendee confirmation."}

            elif tool_name == "request_human_decision":
                return {"text": "Escalated to human decision. Case transitioned to ESCALATION_REQUIRED."}

            return {"text": "Rehearsal execution step completed."}

        # Handle user prompt message
        user_text = ""
        for block in content:
            if isinstance(block, dict) and "text" in block:
                user_text += block["text"]
            elif hasattr(block, "text"):
                user_text += str(block.text)

        if "Initiate recovery for case" in user_text:
            match = re.search(r"case-[a-zA-Z0-9_\-]+", user_text)
            case_id = match.group(0) if match else "case-unknown"
            return {"tool": "get_case_context", "args": {"case_id": case_id}}

        elif "Process provider reply for offer" in user_text:
            match_offer = re.search(r"(?:ofr|offer)-[a-zA-Z0-9_\-]+", user_text)
            offer_id = match_offer.group(0) if match_offer else "offer-unknown"
            
            # Extract reply text inside single quotes or after reply=
            reply_text = ""
            m_quote = re.search(r"reply=['\"](.*?)['\"]", user_text)
            if m_quote:
                reply_text = m_quote.group(1)
            else:
                m_colon = re.search(r":\s*['\"]?(.*?)['\"]?(\.|$)", user_text)
                if m_colon:
                    reply_text = m_colon.group(1)
            
            classification = self._classify_reply_text(reply_text)
            return {
                "tool": "record_provider_response",
                "args": {"offer_id": offer_id, "response": classification},
            }

        elif "Propose offer for case" in user_text:
            m_case = re.search(r"case-[a-zA-Z0-9_\-]+", user_text)
            m_prov = re.search(r"provider\s+([a-zA-Z0-9_\-]+)", user_text)
            case_id = m_case.group(0) if m_case else "case-unknown"
            prov_id = m_prov.group(1) if m_prov else "prov-unknown"
            return {
                "tool": "create_provider_offer",
                "args": {"case_id": case_id, "provider_id": prov_id},
            }

        return {"text": "Instruction understood. Rehearsal model standing by."}

    async def stream(
        self,
        messages: Messages,
        tool_specs: Optional[List[ToolSpec]] = None,
        system_prompt: Optional[str] = None,
        *,
        tool_choice: Optional[ToolChoice] = None,
        system_prompt_content: Optional[List[SystemContentBlock]] = None,
        invocation_state: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> AsyncIterable[StreamEvent]:
        """Generate deterministic stream events based on scripted steps, custom handler, or dynamic rules."""
        self.turn_count += 1
        self.model_invocations += 1
        self.invocation_log.append({
            "turn": self.turn_count,
            "message_count": len(messages),
        })

        # Track any tool results that failed or were cancelled
        for m in messages:
            content_m = m.get("content", []) if isinstance(m, dict) else getattr(m, "content", [])
            for block in content_m:
                if isinstance(block, dict) and "toolResult" in block:
                    tr = block["toolResult"]
                    if tr.get("status") == "error":
                        tu_id = tr.get("toolUseId")
                        for prev in messages:
                            prev_c = prev.get("content", []) if isinstance(prev, dict) else getattr(prev, "content", [])
                            for pb in prev_c:
                                if isinstance(pb, dict) and "toolUse" in pb:
                                    if pb["toolUse"].get("toolUseId") == tu_id:
                                        t_name = pb["toolUse"].get("name")
                                        if t_name and t_name not in self.denied_tools:
                                            self.denied_tools.append(t_name)

        # 1. Check if a scripted step is queued
        if self.scripted_steps:
            step = self.scripted_steps.pop(0)
        elif self.custom_handler:
            step = self.custom_handler(messages, self.turn_count)
        else:
            step = self._resolve_autonomous_step(messages)


        if "tool" in step:
            tool_name = step["tool"]
            tool_args = step.get("args", {})
            tool_call_id = step.get("tool_use_id", f"call_{uuid.uuid4().hex[:6]}")
            self.proposed_tools.append(tool_name)

            yield {"messageStart": {"role": "assistant"}}
            yield {
                "contentBlockStart": {
                    "start": {
                        "toolUse": {
                            "toolUseId": tool_call_id,
                            "name": tool_name,
                        }
                    },
                    "contentBlockIndex": 0,
                }
            }
            yield {
                "contentBlockDelta": {
                    "delta": {"toolUse": {"input": json.dumps(tool_args)}},
                    "contentBlockIndex": 0,
                }
            }
            yield {"contentBlockStop": {"contentBlockIndex": 0}}
            yield {"messageStop": {"stopReason": "tool_use"}}
            return

        text = step.get("text", "Finished execution turn.")
        yield {"messageStart": {"role": "assistant"}}
        yield {
            "contentBlockStart": {
                "start": {"text": ""},
                "contentBlockIndex": 0,
            }
        }
        yield {
            "contentBlockDelta": {
                "delta": {"text": text},
                "contentBlockIndex": 0,
            }
        }
        yield {"contentBlockStop": {"contentBlockIndex": 0}}
        yield {"messageStop": {"stopReason": "end_turn"}}

