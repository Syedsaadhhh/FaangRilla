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


class BedrockModelAdapter:
    """Configurable Amazon Bedrock model adapter.
    
    Adheres strictly to the verification contract:
    - Never fabricates live model responses when credentials are missing.
    - Accurately reports BLOCKED_BY_ACCESS when credentials/quotas are unavailable.
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
        """Run a non-destructive Bedrock smoke test or return BLOCKED_BY_ACCESS."""
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


class RehearsalModel(Model):
    """Deterministic Rehearsal Model for offline testing and synthetic evaluation.
    
    Clearly labeled: NOT live Bedrock. Provides deterministic rule-based tool
    execution and language classification according to domain specifications.
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
        """Generate deterministic stream events based on scripted steps or message history."""
        self.turn_count += 1
        self.invocation_log.append({
            "turn": self.turn_count,
            "message_count": len(messages),
        })

        # 1. Check if a scripted step is queued
        if self.scripted_steps:
            step = self.scripted_steps.pop(0)
            if "tool" in step:
                tool_name = step["tool"]
                tool_args = step.get("args", {})
                tool_call_id = step.get("tool_use_id", f"call_{uuid.uuid4().hex[:6]}")

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

            if "text" in step:
                text = step["text"]
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
                return

        # 2. Check if a custom handler is defined
        if self.custom_handler:
            result = self.custom_handler(messages, self.turn_count)
            if "tool" in result:
                tool_name = result["tool"]
                tool_args = result.get("args", {})
                tool_call_id = result.get("tool_use_id", f"call_{uuid.uuid4().hex[:6]}")
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

            text = result.get("text", "Finished.")
            yield {"messageStart": {"role": "assistant"}}
            yield {
                "contentBlockStart": {"start": {"text": ""}, "contentBlockIndex": 0}
            }
            yield {
                "contentBlockDelta": {"delta": {"text": text}, "contentBlockIndex": 0}
            }
            yield {"contentBlockStop": {"contentBlockIndex": 0}}
            yield {"messageStop": {"stopReason": "end_turn"}}
            return

        # 3. Default fallback: synthesize end_turn
        yield {"messageStart": {"role": "assistant"}}
        yield {"contentBlockStart": {"start": {"text": ""}, "contentBlockIndex": 0}}
        yield {
            "contentBlockDelta": {
                "delta": {"text": "Rehearsal model finished execution turn."},
                "contentBlockIndex": 0,
            }
        }
        yield {"contentBlockStop": {"contentBlockIndex": 0}}
        yield {"messageStop": {"stopReason": "end_turn"}}
