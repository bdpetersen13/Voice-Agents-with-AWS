"""
Tool Processor
Central processor for all restaurant agent tools
"""
import asyncio
import json
import uuid
import boto3
from utils.logging import debug_print
from config.settings import get_config
from config.constants import (
    TOOL_LOOKUP_RESERVATION,
    TOOL_CREATE_RESERVATION,
    TOOL_EDIT_RESERVATION,
    TOOL_CANCEL_RESERVATION,
    TOOL_CONFIRM_RESERVATION,
    TOOL_JOIN_WAITLIST,
    TOOL_CHECK_WAIT_TIME,
    TOOL_NOTIFY_TABLE_READY,
    TOOL_SEAT_GUEST,
    TOOL_PLACE_ORDER,
    TOOL_VIEW_MENU,
    TOOL_CHECK_ORDER_STATUS,
)
from tools import (
    LookupReservationTool,
    CreateReservationTool,
    EditReservationTool,
    CancelReservationTool,
    ConfirmReservationTool,
    JoinWaitlistTool,
    CheckWaitTimeTool,
    NotifyTableReadyTool,
    SeatGuestTool,
    PlaceOrderTool,
    CheckOrderStatusTool,
    ViewMenuTool,
)


class RestaurantToolProcessor:
    """Handles all restaurant voice agent tools with DynamoDB integration"""

    def __init__(self):
        self.tasks = {}
        config = get_config()

        # Initialize DynamoDB
        self.dynamodb = boto3.resource("dynamodb", region_name=config.aws_region)

        # Initialize all tools
        self.tools = {
            TOOL_LOOKUP_RESERVATION: LookupReservationTool(self.dynamodb),
            TOOL_CREATE_RESERVATION: CreateReservationTool(self.dynamodb),
            TOOL_EDIT_RESERVATION: EditReservationTool(self.dynamodb),
            TOOL_CANCEL_RESERVATION: CancelReservationTool(self.dynamodb),
            TOOL_CONFIRM_RESERVATION: ConfirmReservationTool(self.dynamodb),
            TOOL_JOIN_WAITLIST: JoinWaitlistTool(self.dynamodb),
            TOOL_CHECK_WAIT_TIME: CheckWaitTimeTool(self.dynamodb),
            TOOL_NOTIFY_TABLE_READY: NotifyTableReadyTool(self.dynamodb),
            TOOL_SEAT_GUEST: SeatGuestTool(self.dynamodb),
            TOOL_PLACE_ORDER: PlaceOrderTool(self.dynamodb),
            TOOL_VIEW_MENU: ViewMenuTool(self.dynamodb),
            TOOL_CHECK_ORDER_STATUS: CheckOrderStatusTool(self.dynamodb),
        }

        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            self.loop = asyncio.get_event_loop()

    async def process_tool_async(self, tool_name, tool_content):
        """Process a tool call asynchronously and return the result"""
        task_id = str(uuid.uuid4())
        task = asyncio.create_task(self._run_tool(tool_name, tool_content))
        self.tasks[task_id] = task

        try:
            result = await task
            return result
        finally:
            if task_id in self.tasks:
                del self.tasks[task_id]

    async def _run_tool(self, tool_name, tool_content):
        """Internal method to execute the tool logic"""
        debug_print(f"Processing tool: {tool_name}")

        # Normalize tool name
        tool = tool_name.lower().replace(" ", "")
        content = tool_content.get("content", {})

        if isinstance(content, str):
            try:
                content_data = json.loads(content)
            except json.JSONDecodeError:
                content_data = {}
        else:
            content_data = content

        # Get the tool handler
        tool_handler = self.tools.get(tool)

        if tool_handler:
            return await self.loop.run_in_executor(None, tool_handler.execute, content_data)
        else:
            return {"error": f"Unsupported tool: {tool_name}"}
