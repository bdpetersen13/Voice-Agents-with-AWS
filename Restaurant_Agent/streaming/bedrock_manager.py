"""
Bedrock Stream Manager
Manages HTTP/2 bidirectional streaming with AWS Bedrock
"""
import asyncio
import base64
import json
from aws_sdk_bedrock_runtime.client import (
    BedrockRuntimeClient,
    InvokeModelWithBidirectionalStreamOperationInput,
)
from aws_sdk_bedrock_runtime.models import (
    InvokeModelWithBidirectionalStreamInputChunk,
    BidirectionalInputPayloadPart,
)
from aws_sdk_bedrock_runtime.config import Config
from smithy_aws_core.identity.environment import EnvironmentCredentialsResolver
from streaming.tool_schemas import get_tool_schemas
from prompts.restaurant_system_prompt import get_system_prompt
from utils.logging import debug_print
from config.constants import MODEL_ID, DEFAULT_AWS_REGION


class BedrockStreamManager:
    """Manages HTTP/2 bidirectional streaming with AWS Bedrock for restaurant agent"""

    # Event templates
    START_SESSION = {
        "modelInput": {
            "systemPrompts": [],
            "messages": [],
        }
    }

    CONTENT_START = {
        "modelInput": {"messages": [{"role": "user", "content": [{"type": "contentStart"}]}]}
    }

    CONTENT_END = {
        "modelInput": {"messages": [{"role": "user", "content": [{"type": "contentEnd"}]}]}
    }

    def __init__(self, tool_processor):
        self.tool_processor = tool_processor
        self.client = None
        self.stream = None
        self.output_queue = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the Bedrock Runtime client"""
        self.client = BedrockRuntimeClient(
            config=Config(
                region=DEFAULT_AWS_REGION,
                credentials_resolver=EnvironmentCredentialsResolver(),
            )
        )

    def start_prompt(self):
        """Returns the tool configuration for restaurant agent"""
        return {
            **self.START_SESSION,
            "modelInput": {
                **self.START_SESSION["modelInput"],
                "toolConfig": {
                    "tools": get_tool_schemas()
                },
            },
        }

    def tool_result_event(self, tool_use_id, result):
        """Create tool result event"""
        return {
            "modelInput": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "toolResult",
                                "toolUseId": tool_use_id,
                                "content": [{"type": "json", "json": json.dumps(result)}],
                            }
                        ],
                    }
                ]
            }
        }

    def initialize_stream(self):
        """Initialize the bidirectional stream with restaurant-specific system prompt"""
        start_prompt = self.start_prompt()
        start_prompt["modelInput"]["systemPrompts"] = [
            {"text": get_system_prompt()}
        ]

        self.stream = self.client.invoke_model_with_bidirectional_stream(
            InvokeModelWithBidirectionalStreamOperationInput(
                model_id=MODEL_ID,
                native_request_payload=json.dumps(start_prompt),
            )
        )
        self.output_queue = asyncio.Queue()

    async def send_raw_event(self, event):
        """Send raw event to Bedrock stream"""
        debug_print(f"Sending event to Bedrock")
        chunk = InvokeModelWithBidirectionalStreamInputChunk(
            chunk_payload_part=BidirectionalInputPayloadPart.from_text(json.dumps(event))
        )
        try:
            self.stream.send_event(chunk)
            debug_print("Event sent successfully")
        except Exception as e:
            print(f"Error sending event: {e}")

    async def _process_audio_input(self, audio_data):
        """Process audio input and send to Bedrock"""
        base64_audio = base64.b64encode(audio_data).decode("utf-8")
        event = {
            "modelInput": {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"type": "audio", "data": base64_audio}],
                    }
                ]
            }
        }
        await self.send_raw_event(event)

    async def send_audio_chunk(self, audio_data):
        """Send audio chunk to stream"""
        await self._process_audio_input(audio_data)

    async def send_content_start(self):
        """Signal start of user input"""
        await self.send_raw_event(self.CONTENT_START)

    async def send_content_end(self):
        """Signal end of user input"""
        await self.send_raw_event(self.CONTENT_END)

    async def process_stream_events(self):
        """Process events from Bedrock stream"""
        try:
            for chunk in self.stream.stream_async():
                if chunk.chunk_payload_part:
                    payload = json.loads(chunk.chunk_payload_part.bytes)

                    if "modelEvent" in payload:
                        model_event = payload["modelEvent"]

                        # Handle tool use
                        if "toolUse" in model_event:
                            tool_use = model_event["toolUse"]
                            tool_name = tool_use.get("name")
                            tool_content = tool_use.get("input", {})
                            tool_use_id = tool_use.get("toolUseId")

                            print(f"\n[Tool Use] {tool_name}")

                            # Execute tool
                            result = await self.tool_processor.process_tool_async(
                                tool_name, {"content": tool_content}
                            )

                            print(f"[Tool Result] {json.dumps(result, indent=2)}")

                            # Send result back
                            result_event = self.tool_result_event(tool_use_id, result)
                            await self.send_raw_event(result_event)

                        # Handle audio output
                        if "audioChunk" in model_event:
                            audio_data = base64.b64decode(model_event["audioChunk"])
                            await self.output_queue.put(audio_data)

                        # Handle text (for debugging)
                        if "textChunk" in model_event:
                            debug_print(f"AI: {model_event['textChunk']}")

        except Exception as e:
            print(f"Error processing stream: {e}")
