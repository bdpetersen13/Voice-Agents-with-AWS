"""
Bedrock Stream Manager
Manages HTTP/2 bidirectional streaming with AWS Bedrock for the banking agent
"""
import json
import base64
import asyncio
from botocore_client_creators import BedrockRuntimeClient
from botocore.config import Config
from botocore.credentials_providers import EnvironmentCredentialsResolver
from botocore_bedrock_runtime_bindings import (
    InvokeModelWithBidirectionalStreamOperationInput,
    InvokeModelWithBidirectionalStreamInputChunk,
    BidirectionalInputPayloadPart,
)
from streaming.tool_schemas import get_tool_schemas
from prompts.banking_system_prompt import get_banking_system_prompt
from utils.logging import debug_print
from config.settings import get_config


class BedrockStreamManager:
    """Manages HTTP/2 bidirectional streaming with AWS Bedrock for banking agent"""

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
        """
        Initialize Bedrock stream manager

        Args:
            tool_processor: Banking tool processor instance for executing tools
        """
        self.tool_processor = tool_processor
        self.client = None
        self.stream = None
        self.output_queue = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the Bedrock Runtime client"""
        config = get_config()
        self.client = BedrockRuntimeClient(
            config=Config(
                region=config.aws_region,
                credentials_resolver=EnvironmentCredentialsResolver(),
            )
        )

    def start_prompt(self):
        """Returns the tool configuration for banking agent with all 21 tools"""
        tools = get_tool_schemas()

        return {
            **self.START_SESSION,
            "modelInput": {
                **self.START_SESSION["modelInput"],
                "toolConfig": {
                    "tools": tools
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
        """Initialize the bidirectional stream with banking-specific system prompt"""
        banking_system_prompt = get_banking_system_prompt()

        start_prompt = self.start_prompt()
        start_prompt["modelInput"]["systemPrompts"] = [
            {"text": banking_system_prompt}
        ]

        self.stream = self.client.invoke_model_with_bidirectional_stream(
            InvokeModelWithBidirectionalStreamOperationInput(
                model_id="amazon.nova-sonic-v1:0",
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
        """Send audio chunk to Bedrock"""
        await self._process_audio_input(audio_data)

    async def send_content_start(self):
        """Send content start event"""
        await self.send_raw_event(self.CONTENT_START)

    async def send_content_end(self):
        """Send content end event"""
        await self.send_raw_event(self.CONTENT_END)

    async def process_stream_events(self):
        """Process events from Bedrock stream"""
        async for event in self.stream:
            if hasattr(event, "chunk_payload_part"):
                payload = json.loads(event.chunk_payload_part.text())
                debug_print(f"Received event: {json.dumps(payload, indent=2)}")

                # Handle audio output
                if "modelOutput" in payload:
                    model_output = payload["modelOutput"]
                    if "content" in model_output:
                        for content_item in model_output["content"]:
                            if content_item.get("type") == "audio":
                                audio_data = base64.b64decode(content_item["data"])
                                await self.output_queue.put(audio_data)

                    # Handle tool use
                    if "toolUse" in model_output:
                        tool_use = model_output["toolUse"]
                        tool_name = tool_use["name"]
                        tool_use_id = tool_use["toolUseId"]
                        tool_content = tool_use.get("input", {})

                        debug_print(f"Tool use: {tool_name}")
                        debug_print(f"Tool content: {json.dumps(tool_content, indent=2)}")

                        # Execute tool
                        result = await self.tool_processor.process_tool_async(
                            tool_name, tool_content
                        )

                        debug_print(f"Tool result: {json.dumps(result, indent=2)}")

                        # Send tool result back to Bedrock
                        tool_result = self.tool_result_event(tool_use_id, result)
                        await self.send_raw_event(tool_result)
