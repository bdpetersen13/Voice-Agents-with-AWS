"""
Call Center Tool Processor
Coordinates tool execution for the call center agent
"""
import asyncio
import json
import uuid
import boto3

from config.constants import (
    TABLE_MEMBERS,
    TABLE_STORE_INFO,
    TABLE_INVENTORY,
    TABLE_CURBSIDE_ORDERS,
    TABLE_APPOINTMENTS,
    TABLE_SPECIALTY_ORDERS,
    DEFAULT_AWS_REGION
)
from tools import (
    VerifyMemberTool,
    CheckStoreHoursTool,
    CheckInventoryTool,
    CheckCurbsideOrderTool,
    CheckSpecialtyOrderTool,
    CreateCakeOrderTool,
    ScheduleAppointmentTool,
    CheckAppointmentTool
)
from utils.logging import debug_print


class CallCenterToolProcessor:
    """Handles all call center tools with DynamoDB integration"""

    def __init__(self):
        self.tasks = {}
        self.dynamodb = boto3.resource("dynamodb", region_name=DEFAULT_AWS_REGION)

        # Initialize DynamoDB tables
        self.members_table = self.dynamodb.Table(TABLE_MEMBERS)
        self.store_info_table = self.dynamodb.Table(TABLE_STORE_INFO)
        self.inventory_table = self.dynamodb.Table(TABLE_INVENTORY)
        self.curbside_table = self.dynamodb.Table(TABLE_CURBSIDE_ORDERS)
        self.appointments_table = self.dynamodb.Table(TABLE_APPOINTMENTS)
        self.specialty_table = self.dynamodb.Table(TABLE_SPECIALTY_ORDERS)

        # Initialize tool instances
        self.verify_member_tool = VerifyMemberTool(self.dynamodb, self.members_table)
        self.check_store_hours_tool = CheckStoreHoursTool(self.dynamodb, self.store_info_table)
        self.check_inventory_tool = CheckInventoryTool(self.dynamodb, self.inventory_table)
        self.check_curbside_tool = CheckCurbsideOrderTool(self.dynamodb, self.curbside_table)
        self.check_specialty_tool = CheckSpecialtyOrderTool(self.dynamodb, self.specialty_table)
        self.create_cake_tool = CreateCakeOrderTool(self.dynamodb, self.specialty_table)
        self.schedule_appointment_tool = ScheduleAppointmentTool(self.dynamodb, self.appointments_table)
        self.check_appointment_tool = CheckAppointmentTool(self.dynamodb, self.appointments_table)

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
        tool = tool_name.lower().replace(" ", "")
        content = tool_content.get("content", {})

        if isinstance(content, str):
            try:
                content_data = json.loads(content)
            except json.JSONDecodeError:
                content_data = {}
        else:
            content_data = content

        # Route to appropriate tool handler
        tool_handlers = {
            "verifymembertool": self.verify_member_tool,
            "checkstorehours tool": self.check_store_hours_tool,
            "checkstorehoorstool": self.check_store_hours_tool,
            "checkinventorytool": self.check_inventory_tool,
            "checkcurbsideordertool": self.check_curbside_tool,
            "scheduleappointmenttool": self.schedule_appointment_tool,
            "checkspecialtyordertool": self.check_specialty_tool,
            "createcakeordertool": self.create_cake_tool,
            "checkappointmenttool": self.check_appointment_tool,
        }

        handler = tool_handlers.get(tool)
        if handler:
            return await self.loop.run_in_executor(None, handler.execute, content_data)
        else:
            return {"error": f"Unsupported tool: {tool_name}"}
