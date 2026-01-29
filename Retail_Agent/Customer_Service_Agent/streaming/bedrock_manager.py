"""
Bedrock Stream Manager for Retail Customer Service Agent
Manages bidirectional streaming with AWS Bedrock using asyncio
"""
import asyncio
import json
import uuid
import base64

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

from config.constants import *
from utils.logging import debug_print
from streaming.tool_schemas import get_tool_schemas


def time_it_async(label, methodToRun):
    """Timing wrapper for async functions"""
    async def wrapper():
        import time
        start_time = time.perf_counter()
        result = await methodToRun()
        end_time = time.perf_counter()
        debug_print(f"Execution time for {label}: {end_time - start_time:.4f} seconds")
        return result
    return wrapper()


class BedrockStreamManager:
    """Manages bidirectional streaming with AWS Bedrock using asyncio"""

    # Event templates (same as hotel agent)
    START_SESSION_EVENT = """{
        "event": {
            "sessionStart": {
            "inferenceConfiguration": {
                "maxTokens": 1024,
                "topP": 0.9,
                "temperature": 0.7
                }
            }
        }
    }"""

    CONTENT_START_EVENT = """{
        "event": {
            "contentStart": {
            "promptName": "%s",
            "contentName": "%s",
            "type": "AUDIO",
            "interactive": true,
            "role": "USER",
            "audioInputConfiguration": {
                "mediaType": "audio/lpcm",
                "sampleRateHertz": 16000,
                "sampleSizeBits": 16,
                "channelCount": 1,
                "audioType": "SPEECH",
                "encoding": "base64"
                }
            }
        }
    }"""

    AUDIO_EVENT_TEMPLATE = """{
        "event": {
            "audioInput": {
            "promptName": "%s",
            "contentName": "%s",
            "content": "%s"
            }
        }
    }"""

    TEXT_CONTENT_START_EVENT = """{
        "event": {
            "contentStart": {
            "promptName": "%s",
            "contentName": "%s",
            "type": "TEXT",
            "role": "%s",
            "interactive": false,
                "textInputConfiguration": {
                    "mediaType": "text/plain"
                }
            }
        }
    }"""

    TEXT_INPUT_EVENT = """{
        "event": {
            "textInput": {
            "promptName": "%s",
            "contentName": "%s",
            "content": "%s"
            }
        }
    }"""

    TOOL_CONTENT_START_EVENT = """{
        "event": {
            "contentStart": {
                "promptName": "%s",
                "contentName": "%s",
                "interactive": false,
                "type": "TOOL",
                "role": "TOOL",
                "toolResultInputConfiguration": {
                    "toolUseId": "%s",
                    "type": "TEXT",
                    "textInputConfiguration": {
                        "mediaType": "text/plain"
                    }
                }
            }
        }
    }"""

    CONTENT_END_EVENT = """{
        "event": {
            "contentEnd": {
            "promptName": "%s",
            "contentName": "%s"
            }
        }
    }"""

    PROMPT_END_EVENT = """{
        "event": {
            "promptEnd": {
            "promptName": "%s"
            }
        }
    }"""

    SESSION_END_EVENT = """{
        "event": {
            "sessionEnd": {}
        }
    }"""

    def start_prompt(self):
        """Create a promptStart event with retail member service tools"""
        tool_schemas = get_tool_schemas()

        prompt_start_event = {
            "event": {
                "promptStart": {
                    "promptName": self.prompt_name,
                    "textOutputConfiguration": {"mediaType": "text/plain"},
                    "audioOutputConfiguration": {
                        "mediaType": "audio/lpcm",
                        "sampleRateHertz": OUTPUT_SAMPLE_RATE,
                        "sampleSizeBits": 16,
                        "channelCount": CHANNELS,
                        "voiceId": "matthew",
                        "encoding": "base64",
                        "audioType": "SPEECH",
                    },
                    "toolUseOutputConfiguration": {"mediaType": "application/json"},
                    "toolConfiguration": {
                        "tools": tool_schemas
                    }
                }
            }
        }

        return json.dumps(prompt_start_event)

    def tool_result_event(self, content_name, content, role):
        """Create a tool result event"""
        if isinstance(content, dict):
            content_json_string = json.dumps(content)
        else:
            content_json_string = content

        tool_result_event = {
            "event": {
                "toolResult": {
                    "promptName": self.prompt_name,
                    "contentName": content_name,
                    "content": content_json_string,
                }
            }
        }
        return json.dumps(tool_result_event)

    def __init__(self, model_id="amazon.nova-sonic-v1:0", region="us-east-1"):
        """Initialize the stream manager."""
        self.model_id = model_id
        self.region = region

        self.audio_input_queue = asyncio.Queue()
        self.audio_output_queue = asyncio.Queue()
        self.output_queue = asyncio.Queue()

        self.response_task = None
        self.stream_response = None
        self.is_active = False
        self.barge_in = False
        self.bedrock_client = None

        self.audio_player = None
        self.display_assistant_text = False
        self.role = None

        self.prompt_name = str(uuid.uuid4())
        self.content_name = str(uuid.uuid4())
        self.audio_content_name = str(uuid.uuid4())
        self.toolUseContent = ""
        self.toolUseId = ""
        self.toolName = ""

        # Add retail tool processor
        from core.retail_tool_processor import RetailToolProcessor
        self.tool_processor = RetailToolProcessor()
        self.pending_tool_tasks = {}

    def _initialize_client(self):
        """Initialize the Bedrock client."""
        config = Config(
            endpoint_uri=f"https://bedrock-runtime.{self.region}.amazonaws.com",
            region=self.region,
            aws_credentials_identity_resolver=EnvironmentCredentialsResolver(),
        )
        self.bedrock_client = BedrockRuntimeClient(config=config)

    async def initialize_stream(self):
        """Initialize the bidirectional stream with Bedrock."""
        if not self.bedrock_client:
            self._initialize_client()

        try:
            self.stream_response = await time_it_async(
                "invoke_model_with_bidirectional_stream",
                lambda: self.bedrock_client.invoke_model_with_bidirectional_stream(
                    InvokeModelWithBidirectionalStreamOperationInput(
                        model_id=self.model_id
                    )
                ),
            )
            self.is_active = True

            # System prompt for retail member service kiosk
            retail_system_prompt = (
                "You are a virtual member service assistant at a retail warehouse club (similar to Costco or Sam's Club). "
                "You're operating from a self-service kiosk at the member service desk. "
                "Your goal is to provide efficient, empathetic service for members who need help with returns, complaints, "
                "transaction issues, or membership changes.\n\n"
                "PERSONALITY:\n"
                "- Warm, professional, and empathetic (acknowledge frustration: 'I understand that's frustrating')\n"
                "- Efficient and solution-oriented (streamline the process vs. waiting in line)\n"
                "- Clear and transparent about policies (90-day return window, refund timelines)\n"
                "- Patient and helpful with technology (members may not be familiar with self-service kiosks)\n\n"
                "SECURITY PROTOCOL:\n"
                "1. ALWAYS start by asking the member to scan their membership barcode using the kiosk scanner.\n"
                "2. Call verifyMemberTool with the scanned memberId.\n"
                "3. Only proceed with other operations after successful verification.\n\n"
                "RETURN PROCESS:\n"
                "1. After member verification, ask: 'What would you like to return today?'\n"
                "2. Call lookupTransactionTool to find their recent purchases.\n"
                "3. Once they identify the item, instruct: 'Please place the item on the return shelf to your right.'\n"
                "4. Call verifyReturnItemTool to use computer vision to verify the item matches the transaction.\n"
                "5. If verified, call initiateReturnTool to process the return and issue refund.\n"
                "6. Provide the return ID and explain refund timeline (3-5 business days).\n\n"
                "TRANSACTION ISSUES:\n"
                "- For double-scans, missed items, or wrong prices: Call lookupTransactionTool for today's transactions.\n"
                "- Use processTransactionIssueTool to create adjustment and issue refund.\n"
                "- Provide reference number and refund timeline.\n\n"
                "MEMBERSHIP CHANGES:\n"
                "- For contact updates: Use modifyMembershipTool (supports phone, email, address, payment method).\n"
                "- For adding household members: Use addHouseholdMemberTool (need name, DOB, relationship).\n"
                "- For removing household members: Use removeHouseholdMemberTool.\n"
                "- Always confirm changes and provide confirmation.\n\n"
                "COMPLAINTS:\n"
                "- Listen empathetically and acknowledge their concern.\n"
                "- Use fileComplaintTool to log the complaint.\n"
                "- Provide reference number and explain a manager will follow up within 24 hours.\n\n"
                "POLICIES:\n"
                "- Return window: 90 days from purchase\n"
                "- Refund timeline: 3-5 business days to original payment method\n"
                "- Some items not returnable: perishables, opened media, etc.\n"
                "- Member verification required for all transactions\n\n"
                "IMPORTANT:\n"
                "- Be concise in your responses (this is voice-based).\n"
                "- Always provide reference numbers for tracking (return IDs, request IDs).\n"
                "- If you can't help with something, offer to connect them with a staff member at the desk.\n"
                "- Never invent data not in the database - if a transaction or member isn't found, say so clearly."
            )

            # Send initialization events
            prompt_event = self.start_prompt()
            text_content_start = self.TEXT_CONTENT_START_EVENT % (
                self.prompt_name,
                self.content_name,
                "SYSTEM",
            )
            text_content = self.TEXT_INPUT_EVENT % (
                self.prompt_name,
                self.content_name,
                retail_system_prompt,
            )
            text_content_end = self.CONTENT_END_EVENT % (
                self.prompt_name,
                self.content_name,
            )

            init_events = [
                self.START_SESSION_EVENT,
                prompt_event,
                text_content_start,
                text_content,
                text_content_end,
            ]

            for event in init_events:
                await self.send_raw_event(event)
                await asyncio.sleep(0.1)

            # Start listening for responses
            self.response_task = asyncio.create_task(self._process_responses())

            # Start processing audio input
            asyncio.create_task(self._process_audio_input())

            await asyncio.sleep(0.1)

            debug_print("Stream initialized successfully")
            return self
        except Exception as e:
            self.is_active = False
            print(f"Failed to initialize stream: {str(e)}")
            raise

    async def send_raw_event(self, event_json):
        """Send a raw event JSON to the Bedrock stream."""
        if not self.stream_response or not self.is_active:
            debug_print("Stream not initialized or closed")
            return

        event = InvokeModelWithBidirectionalStreamInputChunk(
            value=BidirectionalInputPayloadPart(bytes_=event_json.encode("utf-8"))
        )

        try:
            await self.stream_response.input_stream.send(event)
            if True:  # Changed from DEBUG flag
                if len(event_json) > 200:
                    event_type = json.loads(event_json).get("event", {}).keys()
                    debug_print(f"Sent event type: {list(event_type)}")
                else:
                    debug_print(f"Sent event: {event_json}")
        except Exception as e:
            debug_print(f"Error sending event: {str(e)}")
            import traceback
            traceback.print_exc()

    async def send_audio_content_start_event(self):
        """Send a content start event to the Bedrock stream."""
        content_start_event = self.CONTENT_START_EVENT % (
            self.prompt_name,
            self.audio_content_name,
        )
        await self.send_raw_event(content_start_event)

    async def _process_audio_input(self):
        """Process audio input from the queue and send to Bedrock."""
        while self.is_active:
            try:
                data = await self.audio_input_queue.get()

                audio_bytes = data.get("audio_bytes")
                if not audio_bytes:
                    debug_print("No audio bytes received")
                    continue

                blob = base64.b64encode(audio_bytes)
                audio_event = self.AUDIO_EVENT_TEMPLATE % (
                    self.prompt_name,
                    self.audio_content_name,
                    blob.decode("utf-8"),
                )

                await self.send_raw_event(audio_event)

            except asyncio.CancelledError:
                break
            except Exception as e:
                debug_print(f"Error processing audio: {e}")
                import traceback
                traceback.print_exc()

    def add_audio_chunk(self, audio_bytes):
        """Add an audio chunk to the queue."""
        self.audio_input_queue.put_nowait(
            {
                "audio_bytes": audio_bytes,
                "prompt_name": self.prompt_name,
                "content_name": self.audio_content_name,
            }
        )

    async def send_audio_content_end_event(self):
        """Send a content end event to the Bedrock stream."""
        if not self.is_active:
            debug_print("Stream is not active")
            return

        content_end_event = self.CONTENT_END_EVENT % (
            self.prompt_name,
            self.audio_content_name,
        )
        await self.send_raw_event(content_end_event)
        debug_print("Audio ended")

    async def send_tool_start_event(self, content_name, tool_use_id):
        """Send a tool content start event to the Bedrock stream."""
        content_start_event = self.TOOL_CONTENT_START_EVENT % (
            self.prompt_name,
            content_name,
            tool_use_id,
        )
        debug_print(f"Sending tool start event: {content_start_event}")
        await self.send_raw_event(content_start_event)

    async def send_tool_result_event(self, content_name, tool_result):
        """Send a tool content event to the Bedrock stream."""
        tool_result_event = self.tool_result_event(
            content_name=content_name, content=tool_result, role="TOOL"
        )
        debug_print(f"Sending tool result event: {tool_result_event}")
        await self.send_raw_event(tool_result_event)

    async def send_tool_content_end_event(self, content_name):
        """Send a tool content end event to the Bedrock stream."""
        tool_content_end_event = self.CONTENT_END_EVENT % (
            self.prompt_name,
            content_name,
        )
        debug_print(f"Sending tool content event: {tool_content_end_event}")
        await self.send_raw_event(tool_content_end_event)

    async def send_prompt_end_event(self):
        """Close the stream and clean up resources."""
        if not self.is_active:
            debug_print("Stream is not active")
            return

        prompt_end_event = self.PROMPT_END_EVENT % (self.prompt_name)
        await self.send_raw_event(prompt_end_event)
        debug_print("Prompt ended")

    async def send_session_end_event(self):
        """Send a session end event to the Bedrock stream."""
        if not self.is_active:
            debug_print("Stream is not active")
            return

        await self.send_raw_event(self.SESSION_END_EVENT)
        self.is_active = False
        debug_print("Session ended")

    async def _process_responses(self):
        """Process incoming responses from Bedrock."""
        try:
            while self.is_active:
                try:
                    output = await self.stream_response.await_output()
                    result = await output[1].receive()
                    if result.value and result.value.bytes_:
                        try:
                            response_data = result.value.bytes_.decode("utf-8")
                            json_data = json.loads(response_data)

                            if "event" in json_data:
                                if "completionStart" in json_data["event"]:
                                    debug_print(f"completionStart: {json_data['event']}")
                                elif "contentStart" in json_data["event"]:
                                    debug_print("Content start detected")
                                    content_start = json_data["event"]["contentStart"]
                                    self.role = content_start["role"]
                                    if "additionalModelFields" in content_start:
                                        try:
                                            additional_fields = json.loads(
                                                content_start["additionalModelFields"]
                                            )
                                            if (
                                                additional_fields.get("generationStage")
                                                == "SPECULATIVE"
                                            ):
                                                debug_print("Speculative content detected")
                                                self.display_assistant_text = True
                                            else:
                                                self.display_assistant_text = False
                                        except json.JSONDecodeError:
                                            debug_print("Error parsing additionalModelFields")
                                elif "textOutput" in json_data["event"]:
                                    text_content = json_data["event"]["textOutput"]["content"]
                                    role = json_data["event"]["textOutput"]["role"]
                                    if '{ "interrupted" : true }' in text_content:
                                        debug_print("Barge-in detected. Stopping audio output.")
                                        self.barge_in = True

                                    if self.role == "ASSISTANT" and self.display_assistant_text:
                                        print(f"Assistant: {text_content}")
                                    elif self.role == "USER":
                                        print(f"User: {text_content}")
                                elif "audioOutput" in json_data["event"]:
                                    audio_content = json_data["event"]["audioOutput"]["content"]
                                    audio_bytes = base64.b64decode(audio_content)
                                    await self.audio_output_queue.put(audio_bytes)
                                elif "toolUse" in json_data["event"]:
                                    self.toolUseContent = json_data["event"]["toolUse"]
                                    self.toolName = json_data["event"]["toolUse"]["toolName"]
                                    self.toolUseId = json_data["event"]["toolUse"]["toolUseId"]
                                    debug_print(f"Tool use detected: {self.toolName}, ID: {self.toolUseId}")
                                elif (
                                    "contentEnd" in json_data["event"]
                                    and json_data["event"].get("contentEnd", {}).get("type") == "TOOL"
                                ):
                                    debug_print("Processing tool use and sending result")
                                    self.handle_tool_request(
                                        self.toolName,
                                        self.toolUseContent,
                                        self.toolUseId,
                                    )
                                    debug_print("Processing tool use asynchronously")
                                elif "contentEnd" in json_data["event"]:
                                    debug_print("Content end")
                                elif "completionEnd" in json_data["event"]:
                                    debug_print("End of response sequence")
                                elif "usageEvent" in json_data["event"]:
                                    debug_print(f"UsageEvent: {json_data['event']}")
                            await self.output_queue.put(json_data)
                        except json.JSONDecodeError:
                            await self.output_queue.put({"raw_data": response_data})
                except StopAsyncIteration:
                    break
                except Exception as e:
                    if "ValidationException" in str(e):
                        error_message = str(e)
                        print(f"Validation error: {error_message}")
                    else:
                        print(f"Error receiving response: {e}")
                    break

        except Exception as e:
            print(f"Response processing error: {e}")
        finally:
            self.is_active = False

    def handle_tool_request(self, tool_name, tool_content, tool_use_id):
        """Handle a tool request asynchronously"""
        tool_content_name = str(uuid.uuid4())

        task = asyncio.create_task(
            self._execute_tool_and_send_result(
                tool_name, tool_content, tool_use_id, tool_content_name
            )
        )

        self.pending_tool_tasks[tool_content_name] = task

        task.add_done_callback(
            lambda t: self._handle_tool_task_completion(t, tool_content_name)
        )

    def _handle_tool_task_completion(self, task, content_name):
        """Handle the completion of a tool task"""
        if content_name in self.pending_tool_tasks:
            del self.pending_tool_tasks[content_name]

        if task.done() and not task.cancelled():
            exception = task.exception()
            if exception:
                debug_print(f"Tool task failed: {str(exception)}")

    async def _execute_tool_and_send_result(
        self, tool_name, tool_content, tool_use_id, content_name
    ):
        """Execute a tool and send the result"""
        try:
            debug_print(f"Starting tool execution: {tool_name}")

            tool_result = await self.tool_processor.process_tool_async(
                tool_name, tool_content
            )

            await self.send_tool_start_event(content_name, tool_use_id)
            await self.send_tool_result_event(content_name, tool_result)
            await self.send_tool_content_end_event(content_name)

            debug_print(f"Tool execution complete: {tool_name}")
        except Exception as e:
            debug_print(f"Error executing tool {tool_name}: {str(e)}")
            try:
                error_result = {"error": f"Tool execution failed: {str(e)}"}

                await self.send_tool_start_event(content_name, tool_use_id)
                await self.send_tool_result_event(content_name, error_result)
                await self.send_tool_content_end_event(content_name)
            except Exception as send_error:
                debug_print(f"Failed to send error response: {str(send_error)}")

    async def close(self):
        """Close the stream properly."""
        if not self.is_active:
            return

        for task in self.pending_tool_tasks.values():
            task.cancel()

        if self.response_task and not self.response_task.done():
            self.response_task.cancel()

        await self.send_audio_content_end_event()
        await self.send_prompt_end_event()
        await self.send_session_end_event()

        if self.stream_response:
            await self.stream_response.input_stream.close()
