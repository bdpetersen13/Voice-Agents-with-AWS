"""
Retail Tool Processor
Handles all retail member service tools with DynamoDB integration
"""
import asyncio
import json
import uuid
from config.settings import get_config
from config.constants import *
from tools import (
    VerifyMemberTool,
    ModifyMembershipTool,
    AddHouseholdMemberTool,
    RemoveHouseholdMemberTool,
    LookupTransactionTool,
    ProcessTransactionIssueTool,
    VerifyReturnItemTool,
    InitiateReturnTool,
    FileComplaintTool,
)
from utils.logging import debug_print


class RetailToolProcessor:
    """Handles all retail member service tools with DynamoDB integration"""

    def __init__(self, dynamodb):
        """
        Initialize the retail tool processor

        Args:
            dynamodb: boto3 DynamoDB resource
        """
        self.tasks = {}
        self.dynamodb = dynamodb
        config = get_config()

        # Initialize DynamoDB tables from config
        self.members_table = self.dynamodb.Table(config.members_table)
        self.transactions_table = self.dynamodb.Table(config.transactions_table)
        self.returns_table = self.dynamodb.Table(config.returns_table)
        self.service_requests_table = self.dynamodb.Table(config.service_requests_table)

        # Initialize all tool instances
        self.tools = self._initialize_tools()

        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            self.loop = asyncio.get_event_loop()

    def _initialize_tools(self):
        """Initialize all 9 retail service tools"""
        return {
            TOOL_VERIFY_MEMBER: VerifyMemberTool(
                self.dynamodb, self.members_table
            ),
            TOOL_LOOKUP_TRANSACTION: LookupTransactionTool(
                self.dynamodb, self.transactions_table
            ),
            TOOL_MODIFY_MEMBERSHIP: ModifyMembershipTool(
                self.dynamodb, self.members_table
            ),
            TOOL_ADD_HOUSEHOLD_MEMBER: AddHouseholdMemberTool(
                self.dynamodb, self.members_table
            ),
            TOOL_REMOVE_HOUSEHOLD_MEMBER: RemoveHouseholdMemberTool(
                self.dynamodb, self.members_table
            ),
            TOOL_VERIFY_RETURN_ITEM: VerifyReturnItemTool(
                self.dynamodb, self.transactions_table
            ),
            TOOL_INITIATE_RETURN: InitiateReturnTool(
                self.dynamodb, self.transactions_table, self.returns_table
            ),
            TOOL_PROCESS_TRANSACTION_ISSUE: ProcessTransactionIssueTool(
                self.dynamodb, self.transactions_table, self.service_requests_table
            ),
            TOOL_FILE_COMPLAINT: FileComplaintTool(
                self.dynamodb, self.service_requests_table
            ),
        }

    async def process_tool_async(self, tool_name, tool_content):
        """
        Process a tool call asynchronously and return the result

        Args:
            tool_name: Name of the tool to execute
            tool_content: Tool parameters

        Returns:
            Dictionary containing tool execution results
        """
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
        """
        Internal method to execute the tool logic

        Args:
            tool_name: Name of the tool
            tool_content: Tool parameters

        Returns:
            Dictionary containing tool execution results
        """
        debug_print(f"Processing tool: {tool_name}")
        
        # Normalize tool name (lowercase, remove spaces)
        tool = tool_name.lower().replace(" ", "")
        content = tool_content.get("content", {})

        # Parse content if it's a JSON string
        if isinstance(content, str):
            try:
                content_data = json.loads(content)
            except json.JSONDecodeError:
                content_data = {}
        else:
            content_data = content

        # Look up tool instance
        tool_instance = self.tools.get(tool)
        
        if tool_instance:
            # Execute tool in thread pool to avoid blocking
            return await self.loop.run_in_executor(
                None, tool_instance.execute, content_data
            )
        else:
            return {"error": f"Unsupported tool: {tool_name}"}
