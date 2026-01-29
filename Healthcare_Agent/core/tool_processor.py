"""
Tool Processor for Healthcare Agent
Manages all 20 HIPAA-compliant tools with proper session management
"""
import json
from typing import Dict, Any, Optional
from config.constants import (
    # Tool names
    TOOL_VERIFY_IDENTITY, TOOL_VERIFY_PHONE, TOOL_VERIFY_EMAIL,
    TOOL_SETUP_PROXY, TOOL_CAPTURE_CONSENT,
    TOOL_SEARCH_AVAILABILITY, TOOL_HOLD_SLOT, TOOL_SCHEDULE_APPOINTMENT,
    TOOL_RESCHEDULE_APPOINTMENT, TOOL_CANCEL_APPOINTMENT,
    TOOL_CONFIRM_APPOINTMENT, TOOL_LOOKUP_APPOINTMENT,
    TOOL_SELECT_PROVIDER, TOOL_SELECT_LOCATION,
    TOOL_CHECK_INSURANCE, TOOL_CHECK_REFERRAL,
    TOOL_START_INTAKE, TOOL_COLLECT_REASON, TOOL_SEND_FORMS,
    TOOL_SEND_PREP_INSTRUCTIONS,
    # Escalation keywords
    ESCALATION_KEYWORDS
)
from tools import (
    # Verification tools
    VerifyIdentityTool, VerifyPhoneTool, VerifyEmailTool,
    SetupProxyTool, CaptureConsentTool,
    # Appointment tools
    SearchAvailabilityTool, HoldSlotTool, ScheduleAppointmentTool,
    RescheduleAppointmentTool, CancelAppointmentTool,
    ConfirmAppointmentTool, LookupAppointmentTool,
    # Provider & Location tools
    SelectProviderTool, SelectLocationTool,
    # Insurance & Referral tools
    CheckInsuranceTool, CheckReferralTool,
    # Intake tools
    StartIntakeTool, CollectReasonTool, SendFormsTool,
    # Prep tools
    SendPrepInstructionsTool
)
from security.session_manager import SessionManager
from security.audit_logger import AuditLogger
from utils.logging import log_info, log_error


class ToolProcessor:
    """Processes tool calls for healthcare agent with HIPAA compliance"""

    def __init__(self, dynamodb, config, session_manager: SessionManager, audit_logger: AuditLogger):
        """
        Initialize tool processor with all 20 healthcare tools

        Args:
            dynamodb: DynamoDB resource
            config: HealthcareConfig instance
            session_manager: Session manager for verification
            audit_logger: Audit logger for PHI access
        """
        self.dynamodb = dynamodb
        self.config = config
        self.session_manager = session_manager
        self.audit_logger = audit_logger

        # Get DynamoDB tables
        self.patients_table = dynamodb.Table(config.table_patients)
        self.appointments_table = dynamodb.Table(config.table_appointments)
        self.providers_table = dynamodb.Table(config.table_providers)
        self.locations_table = dynamodb.Table(config.table_locations)
        self.availability_table = dynamodb.Table(config.table_availability)
        self.insurance_table = dynamodb.Table(config.table_insurance)
        self.referrals_table = dynamodb.Table(config.table_referrals)
        self.intake_forms_table = dynamodb.Table(config.table_intake_forms)

        # Initialize all tools
        self.tools = self._initialize_tools()

        log_info("ToolProcessor initialized with 20 HIPAA-compliant tools")

    def _initialize_tools(self) -> Dict[str, Any]:
        """Initialize and register all 20 healthcare tools"""

        # Verification Tools (5)
        verify_identity = VerifyIdentityTool(
            self.dynamodb,
            self.patients_table,
            self.session_manager,
            self.audit_logger
        )

        verify_phone = VerifyPhoneTool(
            self.dynamodb,
            self.patients_table,
            self.session_manager,
            self.audit_logger
        )

        verify_email = VerifyEmailTool(
            self.dynamodb,
            self.patients_table,
            self.session_manager,
            self.audit_logger
        )

        setup_proxy = SetupProxyTool(
            self.dynamodb,
            self.patients_table,
            self.session_manager,
            self.audit_logger
        )

        capture_consent = CaptureConsentTool(
            self.dynamodb,
            self.session_manager,
            self.audit_logger
        )

        # Appointment Tools (7)
        search_availability = SearchAvailabilityTool(
            self.dynamodb,
            self.availability_table,
            self.providers_table,
            self.locations_table,
            self.audit_logger
        )

        hold_slot = HoldSlotTool(
            self.dynamodb,
            self.availability_table,
            self.audit_logger
        )

        schedule_appointment = ScheduleAppointmentTool(
            self.dynamodb,
            self.appointments_table,
            self.availability_table,
            self.patients_table,
            self.session_manager,
            self.audit_logger
        )

        reschedule_appointment = RescheduleAppointmentTool(
            self.dynamodb,
            self.appointments_table,
            self.availability_table,
            self.session_manager,
            self.audit_logger
        )

        cancel_appointment = CancelAppointmentTool(
            self.dynamodb,
            self.appointments_table,
            self.availability_table,
            self.session_manager,
            self.audit_logger
        )

        confirm_appointment = ConfirmAppointmentTool(
            self.dynamodb,
            self.appointments_table,
            self.audit_logger
        )

        lookup_appointment = LookupAppointmentTool(
            self.dynamodb,
            self.appointments_table,
            self.session_manager,
            self.audit_logger
        )

        # Provider & Location Tools (2)
        select_provider = SelectProviderTool(
            self.dynamodb,
            self.providers_table,
            self.audit_logger
        )

        select_location = SelectLocationTool(
            self.dynamodb,
            self.locations_table,
            self.audit_logger
        )

        # Insurance & Referral Tools (2)
        check_insurance = CheckInsuranceTool(
            self.dynamodb,
            self.insurance_table,
            self.patients_table,
            self.session_manager,
            self.audit_logger
        )

        check_referral = CheckReferralTool(
            self.dynamodb,
            self.referrals_table,
            self.patients_table,
            self.session_manager,
            self.audit_logger
        )

        # Intake Tools (3)
        start_intake = StartIntakeTool(
            self.dynamodb,
            self.patients_table,
            self.intake_forms_table,
            self.session_manager,
            self.audit_logger
        )

        collect_reason = CollectReasonTool(
            self.dynamodb,
            self.intake_forms_table,
            self.audit_logger
        )

        send_forms = SendFormsTool(
            self.dynamodb,
            self.intake_forms_table,
            self.patients_table,
            self.audit_logger
        )

        # Prep Tools (1)
        send_prep_instructions = SendPrepInstructionsTool(
            self.dynamodb,
            self.appointments_table,
            self.patients_table,
            self.audit_logger
        )

        # Register all tools
        return {
            # Verification (5)
            TOOL_VERIFY_IDENTITY: verify_identity,
            TOOL_VERIFY_PHONE: verify_phone,
            TOOL_VERIFY_EMAIL: verify_email,
            TOOL_SETUP_PROXY: setup_proxy,
            TOOL_CAPTURE_CONSENT: capture_consent,

            # Appointments (7)
            TOOL_SEARCH_AVAILABILITY: search_availability,
            TOOL_HOLD_SLOT: hold_slot,
            TOOL_SCHEDULE_APPOINTMENT: schedule_appointment,
            TOOL_RESCHEDULE_APPOINTMENT: reschedule_appointment,
            TOOL_CANCEL_APPOINTMENT: cancel_appointment,
            TOOL_CONFIRM_APPOINTMENT: confirm_appointment,
            TOOL_LOOKUP_APPOINTMENT: lookup_appointment,

            # Provider & Location (2)
            TOOL_SELECT_PROVIDER: select_provider,
            TOOL_SELECT_LOCATION: select_location,

            # Insurance & Referral (2)
            TOOL_CHECK_INSURANCE: check_insurance,
            TOOL_CHECK_REFERRAL: check_referral,

            # Intake (3)
            TOOL_START_INTAKE: start_intake,
            TOOL_COLLECT_REASON: collect_reason,
            TOOL_SEND_FORMS: send_forms,

            # Prep (1)
            TOOL_SEND_PREP_INSTRUCTIONS: send_prep_instructions,
        }

    def process_tool_use(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """
        Process a tool call from Claude

        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool

        Returns:
            JSON string with tool result
        """
        try:
            log_info(f"Processing tool: {tool_name}")

            # Check for escalation keywords in any text input
            if self._should_escalate(tool_input):
                log_info(f"Escalation triggered for tool {tool_name}")
                return json.dumps({
                    "escalate": True,
                    "reason": "Medical detail detected - must escalate to clinical staff",
                    "message": "I've detected a medical topic that I'm not able to discuss. Let me connect you with our clinical staff who can help you with that."
                })

            # Get the tool
            tool = self.tools.get(tool_name)

            if not tool:
                log_error(f"Unknown tool: {tool_name}")
                return json.dumps({
                    "error": f"Unknown tool: {tool_name}"
                })

            # Execute the tool
            result = tool.execute(tool_input)

            # Convert result to JSON
            result_json = json.dumps(result, default=str)

            log_info(f"Tool {tool_name} executed successfully")
            return result_json

        except Exception as e:
            log_error(f"Error processing tool {tool_name}: {str(e)}")
            return json.dumps({
                "error": f"Error executing {tool_name}: {str(e)}"
            })

    def _should_escalate(self, tool_input: Dict[str, Any]) -> bool:
        """
        Check if input contains escalation keywords (medical details)

        Args:
            tool_input: Tool input parameters

        Returns:
            True if escalation is needed
        """
        # Convert all input values to lowercase string for checking
        input_text = json.dumps(tool_input).lower()

        # Check for escalation keywords
        for keyword in ESCALATION_KEYWORDS:
            if keyword.lower() in input_text:
                return True

        return False

    def get_available_tools(self) -> list:
        """
        Get list of available tool names

        Returns:
            List of tool names
        """
        return list(self.tools.keys())

    def get_tool_count(self) -> int:
        """
        Get total number of registered tools

        Returns:
            Tool count
        """
        return len(self.tools)
