"""
Banking Tool Processor
Handles routing of tool calls to appropriate tool instances
"""
import json
import uuid
import asyncio
import boto3
from config.settings import get_config
from config.constants import *
from core.authentication import BankingAuthenticationManager
from tools.authentication_tools import AuthenticateTool, VerifyOtpTool, StepUpAuthenticationTool
from tools.account_tools import CheckBalanceTool, ViewRecentTransactionsTool, SearchTransactionsTool, RequestStatementTool
from tools.card_tools import ReportLostCardTool, FreezeCardTool, UnfreezeCardTool, CheckReplacementStatusTool, DisputeChargeTool, ClarifyMerchantTool
from tools.payment_tools import InternalTransferTool, CheckZelleStatusTool, SetupBillpayTool, StopPaymentTool, ExplainPendingTool
from tools.fraud_tools import ReportFraudTool, CheckDisputeStatusTool, ExplainProvisionalCreditTool
from utils.logging import debug_print


class BankingToolProcessor:
    """Handles all banking customer service tools with security and compliance"""

    def __init__(self, dynamodb, auth_manager):
        """
        Initialize banking tool processor

        Args:
            dynamodb: DynamoDB resource
            auth_manager: BankingAuthenticationManager instance
        """
        self.tasks = {}
        self.dynamodb = dynamodb
        self.auth_manager = auth_manager

        # Current session (in production, would be per-user)
        self.current_session_id = None

        # Get configuration
        config = get_config()

        # Initialize all DynamoDB tables
        self.customers_table = self.dynamodb.Table(config.customers_table)
        self.accounts_table = self.dynamodb.Table(config.accounts_table)
        self.transactions_table = self.dynamodb.Table(config.transactions_table)
        self.cards_table = self.dynamodb.Table(config.cards_table)
        self.disputes_table = self.dynamodb.Table(config.disputes_table)
        self.transfers_table = self.dynamodb.Table(config.transfers_table)
        self.billpay_table = self.dynamodb.Table(config.billpay_table)

        # Initialize all tool instances
        self.tools = self._initialize_tools()

        # Get or create event loop
        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            self.loop = asyncio.get_event_loop()

    def _initialize_tools(self):
        """Initialize all 21 banking tool instances"""
        return {
            # Authentication Tools (3)
            TOOL_AUTHENTICATE: AuthenticateTool(
                self.dynamodb, self.auth_manager, self.customers_table
            ),
            TOOL_VERIFY_OTP: VerifyOtpTool(
                self.dynamodb, self.auth_manager
            ),
            TOOL_STEP_UP_AUTHENTICATION: StepUpAuthenticationTool(
                self.dynamodb, self.auth_manager
            ),

            # Account Information Tools (4)
            TOOL_CHECK_BALANCE: CheckBalanceTool(
                self.dynamodb, self.auth_manager, self.accounts_table
            ),
            TOOL_VIEW_RECENT_TRANSACTIONS: ViewRecentTransactionsTool(
                self.dynamodb, self.auth_manager, self.transactions_table
            ),
            TOOL_SEARCH_TRANSACTIONS: SearchTransactionsTool(
                self.dynamodb, self.auth_manager, self.transactions_table
            ),
            TOOL_REQUEST_STATEMENT: RequestStatementTool(
                self.dynamodb, self.auth_manager, self.accounts_table, self.customers_table
            ),

            # Card Services Tools (6)
            TOOL_REPORT_LOST_CARD: ReportLostCardTool(
                self.dynamodb, self.auth_manager, self.cards_table
            ),
            TOOL_FREEZE_CARD: FreezeCardTool(
                self.dynamodb, self.auth_manager, self.cards_table
            ),
            TOOL_UNFREEZE_CARD: UnfreezeCardTool(
                self.dynamodb, self.auth_manager, self.cards_table
            ),
            TOOL_CHECK_REPLACEMENT_STATUS: CheckReplacementStatusTool(
                self.dynamodb, self.auth_manager, self.cards_table
            ),
            TOOL_DISPUTE_CHARGE: DisputeChargeTool(
                self.dynamodb, self.auth_manager, self.transactions_table, self.disputes_table
            ),
            TOOL_CLARIFY_MERCHANT: ClarifyMerchantTool(
                self.dynamodb, self.auth_manager, self.transactions_table
            ),

            # Payment & Transfer Tools (5)
            TOOL_INTERNAL_TRANSFER: InternalTransferTool(
                self.dynamodb, self.auth_manager, self.accounts_table, self.transfers_table
            ),
            TOOL_CHECK_ZELLE_STATUS: CheckZelleStatusTool(
                self.dynamodb, self.auth_manager, self.transfers_table
            ),
            TOOL_SETUP_BILLPAY: SetupBillpayTool(
                self.dynamodb, self.auth_manager, self.accounts_table, self.billpay_table
            ),
            TOOL_STOP_PAYMENT: StopPaymentTool(
                self.dynamodb, self.auth_manager, self.accounts_table
            ),
            TOOL_EXPLAIN_PENDING: ExplainPendingTool(
                self.dynamodb, self.auth_manager
            ),

            # Fraud & Dispute Tools (3)
            TOOL_REPORT_FRAUD: ReportFraudTool(
                self.dynamodb, self.auth_manager, self.cards_table
            ),
            TOOL_CHECK_DISPUTE_STATUS: CheckDisputeStatusTool(
                self.dynamodb, self.auth_manager, self.disputes_table
            ),
            TOOL_EXPLAIN_PROVISIONAL_CREDIT: ExplainProvisionalCreditTool(
                self.dynamodb, self.auth_manager
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
            # Set current session ID on tool instance
            tool_instance.set_session_id(self.current_session_id)

            # Execute tool in executor (to handle synchronous tool code)
            result = await self.loop.run_in_executor(
                None, tool_instance.execute, content_data
            )

            # Update current session ID if authentication tool
            if tool == TOOL_AUTHENTICATE and result.get("authenticated"):
                self.current_session_id = result.get("sessionId")
                # Update all tool instances with new session ID
                for t in self.tools.values():
                    t.set_session_id(self.current_session_id)

            return result
        else:
            return {"error": f"Unsupported tool: {tool_name}"}
