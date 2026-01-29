"""
Constants Module
All magic numbers and constant values for the healthcare appointment scheduling agent

HIPAA Compliance Note: This module contains configuration constants only.
No PHI (Protected Health Information) is stored here.
"""
import pyaudio

# Audio Configuration
INPUT_SAMPLE_RATE = 16000
OUTPUT_SAMPLE_RATE = 24000
CHANNELS = 1
AUDIO_FORMAT = pyaudio.paInt16
CHUNK_SIZE = 1024

# AWS Configuration
DEFAULT_AWS_REGION = "us-east-1"

# DynamoDB Table Names
TABLE_PATIENTS = "Healthcare_Patients"
TABLE_APPOINTMENTS = "Healthcare_Appointments"
TABLE_PROVIDERS = "Healthcare_Providers"
TABLE_LOCATIONS = "Healthcare_Locations"
TABLE_AVAILABILITY = "Healthcare_Availability"
TABLE_INSURANCE = "Healthcare_Insurance"
TABLE_REFERRALS = "Healthcare_Referrals"
TABLE_INTAKE_FORMS = "Healthcare_Intake_Forms"
TABLE_AUDIT_LOGS = "Healthcare_Audit_Logs"
TABLE_SESSIONS = "Healthcare_Sessions"

# Bedrock Model Configuration
MODEL_MAX_TOKENS = 1024
MODEL_TOP_P = 0.9
MODEL_TEMPERATURE = 0.7

# HIPAA Compliance Settings
SESSION_TIMEOUT_MINUTES = 15  # Auto-logout after 15 minutes inactivity
SESSION_WARNING_MINUTES = 13  # Warn at 13 minutes
MAX_VERIFICATION_ATTEMPTS = 3
REQUIRE_EXPLICIT_CONSENT = True
MINIMUM_NECESSARY_PRINCIPLE = True  # Only access data needed for task

# Audit Logging
ENABLE_AUDIT_LOGGING = True
LOG_ALL_PHI_ACCESS = True
LOG_VERIFICATION_ATTEMPTS = True
LOG_CONSENT_CAPTURE = True

# Identity Verification Levels
VERIFICATION_LEVEL_NONE = 0
VERIFICATION_LEVEL_LIGHT = 1  # Name + DOB
VERIFICATION_LEVEL_STANDARD = 2  # Light + Phone/Email
VERIFICATION_LEVEL_FULL = 3  # Standard + MRN/Patient ID

# Appointment Types
APPT_TYPE_NEW_PATIENT = "new_patient"
APPT_TYPE_FOLLOW_UP = "follow_up"
APPT_TYPE_PROCEDURE = "procedure"
APPT_TYPE_CONSULTATION = "consultation"
APPT_TYPE_SCREENING = "screening"
APPT_TYPE_URGENT = "urgent_care"

# Appointment Status
APPT_STATUS_SCHEDULED = "scheduled"
APPT_STATUS_CONFIRMED = "confirmed"
APPT_STATUS_PENDING = "pending"
APPT_STATUS_CANCELLED = "cancelled"
APPT_STATUS_COMPLETED = "completed"
APPT_STATUS_NO_SHOW = "no_show"

# Slot Availability
SLOT_AVAILABLE = "available"
SLOT_HELD = "held"
SLOT_BOOKED = "booked"
SLOT_BLOCKED = "blocked"

# Hold Time (for slot reservation during booking)
SLOT_HOLD_MINUTES = 10

# Insurance Verification
INSURANCE_VERIFIED = "verified"
INSURANCE_PENDING = "pending"
INSURANCE_FAILED = "failed"
INSURANCE_NOT_REQUIRED = "not_required"

# Referral Status
REFERRAL_REQUIRED = "required"
REFERRAL_RECEIVED = "received"
REFERRAL_NOT_REQUIRED = "not_required"
REFERRAL_PENDING = "pending"

# Tool Names (normalized for lookup)
TOOL_VERIFY_IDENTITY = "verifyidentity"
TOOL_VERIFY_PHONE = "verifyphone"
TOOL_VERIFY_EMAIL = "verifyemail"
TOOL_SETUP_PROXY = "setupproxy"
TOOL_CAPTURE_CONSENT = "captureconsent"

TOOL_SEARCH_AVAILABILITY = "searchavailability"
TOOL_HOLD_SLOT = "holdslot"
TOOL_SCHEDULE_APPOINTMENT = "scheduleappointment"
TOOL_RESCHEDULE_APPOINTMENT = "rescheduleappointment"
TOOL_CANCEL_APPOINTMENT = "cancelappointment"
TOOL_CONFIRM_APPOINTMENT = "confirmappointment"
TOOL_LOOKUP_APPOINTMENT = "lookupappointment"

TOOL_SELECT_PROVIDER = "selectprovider"
TOOL_SELECT_LOCATION = "selectlocation"
TOOL_CHECK_INSURANCE = "checkinsurance"
TOOL_CHECK_REFERRAL = "checkreferral"

TOOL_START_INTAKE = "startintake"
TOOL_COLLECT_REASON = "collectreason"
TOOL_SEND_FORMS = "sendforms"
TOOL_SEND_PREP_INSTRUCTIONS = "sendprepinstructions"

# Escalation Triggers (HIPAA: Don't discuss medical details)
ESCALATION_KEYWORDS = [
    "diagnosis", "medication", "prescription", "test results", 
    "medical records", "treatment", "symptoms", "pain level",
    "lab results", "imaging", "x-ray", "mri", "scan"
]
