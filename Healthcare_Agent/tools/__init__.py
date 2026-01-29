"""
Tools Module
All healthcare appointment scheduling tools
"""
from tools.base_tool import BaseTool
from tools.verification_tools import (
    VerifyIdentityTool, VerifyPhoneTool, VerifyEmailTool,
    SetupProxyTool, CaptureConsentTool
)
from tools.appointment_tools import (
    SearchAvailabilityTool, HoldSlotTool, ScheduleAppointmentTool,
    RescheduleAppointmentTool, CancelAppointmentTool,
    ConfirmAppointmentTool, LookupAppointmentTool
)
from tools.provider_tools import (
    SelectProviderTool, SelectLocationTool
)
from tools.insurance_tools import (
    CheckInsuranceTool, CheckReferralTool
)
from tools.intake_tools import (
    StartIntakeTool, CollectReasonTool, SendFormsTool
)
from tools.prep_tools import (
    SendPrepInstructionsTool
)

__all__ = [
    "BaseTool",
    # Verification (5 tools)
    "VerifyIdentityTool",
    "VerifyPhoneTool",
    "VerifyEmailTool",
    "SetupProxyTool",
    "CaptureConsentTool",
    # Appointments (7 tools)
    "SearchAvailabilityTool",
    "HoldSlotTool",
    "ScheduleAppointmentTool",
    "RescheduleAppointmentTool",
    "CancelAppointmentTool",
    "ConfirmAppointmentTool",
    "LookupAppointmentTool",
    # Provider & Location (2 tools)
    "SelectProviderTool",
    "SelectLocationTool",
    # Insurance & Referral (2 tools)
    "CheckInsuranceTool",
    "CheckReferralTool",
    # Intake (3 tools)
    "StartIntakeTool",
    "CollectReasonTool",
    "SendFormsTool",
    # Prep (1 tool)
    "SendPrepInstructionsTool",
]
