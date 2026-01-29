"""
Hotel Tool Processor
Handles routing of tool calls to appropriate tool instances
"""
import json
import uuid
import asyncio
from config.settings import get_config
from config.constants import *
from tools.guest_tools import CheckGuestProfileTool
from tools.reservation_tools import CheckReservationStatusTool, UpdateReservationTool
from utils.logging import debug_print


class HotelToolProcessor:
    """Handles all hotel service tools"""

    def __init__(self, dynamodb):
        """
        Initialize hotel tool processor

        Args:
            dynamodb: DynamoDB resource
        """
        self.tasks = {}
        self.dynamodb = dynamodb

        # Get configuration
        config = get_config()

        # Initialize all DynamoDB tables
        self.guests_table = self.dynamodb.Table(config.guests_table)
        self.reservations_table = self.dynamodb.Table(config.reservations_table)

        # Initialize all tool instances
        self.tools = self._initialize_tools()

        # Get or create event loop
        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            self.loop = asyncio.get_event_loop()

    def _initialize_tools(self):
        """Initialize all 3 hotel tool instances"""
        return {
            # Guest Tools (1)
            TOOL_CHECK_GUEST_PROFILE: CheckGuestProfileTool(
                self.dynamodb, self.guests_table
            ),

            # Reservation Tools (2)
            TOOL_CHECK_RESERVATION_STATUS: CheckReservationStatusTool(
                self.dynamodb, self.reservations_table
            ),
            TOOL_UPDATE_RESERVATION: UpdateReservationTool(
                self.dynamodb, self.reservations_table
            ),
        }

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

        # Normalize tool name to match constants
        tool = tool_name.lower().replace(" ", "")

        # Extract content data
        content = tool_content.get("content", {})
        if isinstance(content, str):
            try:
                content_data = json.loads(content)
            except json.JSONDecodeError:
                content_data = {}
        else:
            content_data = content

        # Get tool instance
        tool_instance = self.tools.get(tool)

        if tool_instance:
            # Execute tool in executor (to handle synchronous tool code)
            result = await self.loop.run_in_executor(
                None, tool_instance.execute, content_data
            )
            return result
        else:
            return {"error": f"Unsupported tool: {tool_name}"}
