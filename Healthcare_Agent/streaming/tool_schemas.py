"""
Tool Schema Definitions for Healthcare Appointment Scheduling Agent
Defines all 20 HIPAA-compliant tools
"""
import json
from config.constants import *


def get_tool_schemas():
    """Returns a list of all tool schema definitions for the healthcare agent"""

    # ========== VERIFICATION TOOLS (5) ==========

    # 1. Verify Identity (Name + DOB) - Level 1
    verify_identity_schema = json.dumps({
        "type": "object",
        "properties": {
            "firstName": {
                "type": "string",
                "description": "Patient's first name"
            },
            "lastName": {
                "type": "string",
                "description": "Patient's last name"
            },
            "dateOfBirth": {
                "type": "string",
                "description": "Patient's date of birth in YYYY-MM-DD format"
            },
            "sessionId": {
                "type": "string",
                "description": "Session identifier for tracking"
            }
        },
        "required": ["firstName", "lastName", "dateOfBirth", "sessionId"]
    })

    # 2. Verify Phone - Level 2
    verify_phone_schema = json.dumps({
        "type": "object",
        "properties": {
            "patientId": {
                "type": "string",
                "description": "Patient ID obtained from identity verification"
            },
            "phoneNumber": {
                "type": "string",
                "description": "Phone number to verify (format: XXX-XXX-XXXX)"
            },
            "sessionId": {
                "type": "string",
                "description": "Session identifier for tracking"
            }
        },
        "required": ["patientId", "phoneNumber", "sessionId"]
    })

    # 3. Verify Email - Level 2
    verify_email_schema = json.dumps({
        "type": "object",
        "properties": {
            "patientId": {
                "type": "string",
                "description": "Patient ID obtained from identity verification"
            },
            "email": {
                "type": "string",
                "description": "Email address to verify"
            },
            "sessionId": {
                "type": "string",
                "description": "Session identifier for tracking"
            }
        },
        "required": ["patientId", "email", "sessionId"]
    })

    # 4. Setup Proxy Access (parent, caregiver, guardian)
    setup_proxy_schema = json.dumps({
        "type": "object",
        "properties": {
            "patientFirstName": {
                "type": "string",
                "description": "Patient's first name"
            },
            "patientLastName": {
                "type": "string",
                "description": "Patient's last name"
            },
            "patientDOB": {
                "type": "string",
                "description": "Patient's date of birth (YYYY-MM-DD)"
            },
            "proxyName": {
                "type": "string",
                "description": "Name of the person calling on behalf of patient"
            },
            "relationship": {
                "type": "string",
                "description": "Relationship to patient (parent, legal_guardian, caregiver, spouse, power_of_attorney)"
            },
            "sessionId": {
                "type": "string",
                "description": "Session identifier for tracking"
            }
        },
        "required": ["patientFirstName", "patientLastName", "patientDOB", "proxyName", "relationship", "sessionId"]
    })

    # 5. Capture Consent
    capture_consent_schema = json.dumps({
        "type": "object",
        "properties": {
            "sessionId": {
                "type": "string",
                "description": "Session identifier for tracking"
            },
            "consentGiven": {
                "type": "boolean",
                "description": "Whether consent is given (true/false)"
            },
            "consentType": {
                "type": "string",
                "description": "Type of consent (appointment_scheduling, phi_access, voice_recording)"
            }
        },
        "required": ["sessionId", "consentGiven", "consentType"]
    })

    # ========== APPOINTMENT TOOLS (7) ==========

    # 6. Search Availability
    search_availability_schema = json.dumps({
        "type": "object",
        "properties": {
            "providerId": {
                "type": "string",
                "description": "Optional: Specific provider ID to search for"
            },
            "locationId": {
                "type": "string",
                "description": "Optional: Specific location ID to search at"
            },
            "specialty": {
                "type": "string",
                "description": "Optional: Medical specialty (primary_care, cardiology, dermatology, etc.)"
            },
            "startDate": {
                "type": "string",
                "description": "Start of date range to search (YYYY-MM-DD)"
            },
            "endDate": {
                "type": "string",
                "description": "Optional: End of date range (defaults to 30 days from startDate)"
            },
            "timePreference": {
                "type": "string",
                "description": "Optional: Time preference (morning, afternoon, evening, after_3pm)"
            },
            "appointmentType": {
                "type": "string",
                "description": "Optional: Type of appointment (new_patient, follow_up, procedure, screening)"
            },
            "sessionId": {
                "type": "string",
                "description": "Session identifier for tracking"
            }
        },
        "required": ["startDate", "sessionId"]
    })

    # 7. Hold Slot (10 minutes)
    hold_slot_schema = json.dumps({
        "type": "object",
        "properties": {
            "slotId": {
                "type": "string",
                "description": "The slot ID to hold from availability search results"
            },
            "sessionId": {
                "type": "string",
                "description": "Session identifier for tracking"
            }
        },
        "required": ["slotId", "sessionId"]
    })

    # 8. Schedule Appointment
    schedule_appointment_schema = json.dumps({
        "type": "object",
        "properties": {
            "patientId": {
                "type": "string",
                "description": "Patient ID (from verification)"
            },
            "slotId": {
                "type": "string",
                "description": "The held slot ID to book"
            },
            "appointmentType": {
                "type": "string",
                "description": "Type of appointment (new_patient, follow_up, procedure, screening, wellness)"
            },
            "reasonCategory": {
                "type": "string",
                "description": "Optional: General reason category (annual_checkup, follow_up, new_concern, procedure, screening)"
            },
            "sessionId": {
                "type": "string",
                "description": "Session identifier for tracking"
            }
        },
        "required": ["patientId", "slotId", "appointmentType", "sessionId"]
    })

    # 9. Reschedule Appointment
    reschedule_appointment_schema = json.dumps({
        "type": "object",
        "properties": {
            "appointmentId": {
                "type": "string",
                "description": "Existing appointment ID to reschedule"
            },
            "patientId": {
                "type": "string",
                "description": "Patient ID (must match appointment owner)"
            },
            "newSlotId": {
                "type": "string",
                "description": "New slot ID for the rescheduled appointment"
            },
            "sessionId": {
                "type": "string",
                "description": "Session identifier for tracking"
            }
        },
        "required": ["appointmentId", "patientId", "newSlotId", "sessionId"]
    })

    # 10. Cancel Appointment
    cancel_appointment_schema = json.dumps({
        "type": "object",
        "properties": {
            "appointmentId": {
                "type": "string",
                "description": "Appointment ID to cancel"
            },
            "patientId": {
                "type": "string",
                "description": "Patient ID (must match appointment owner)"
            },
            "sessionId": {
                "type": "string",
                "description": "Session identifier for tracking"
            }
        },
        "required": ["appointmentId", "patientId", "sessionId"]
    })

    # 11. Confirm Appointment
    confirm_appointment_schema = json.dumps({
        "type": "object",
        "properties": {
            "appointmentId": {
                "type": "string",
                "description": "Appointment ID to confirm"
            },
            "sessionId": {
                "type": "string",
                "description": "Session identifier for tracking"
            }
        },
        "required": ["appointmentId", "sessionId"]
    })

    # 12. Lookup Appointments
    lookup_appointment_schema = json.dumps({
        "type": "object",
        "properties": {
            "patientId": {
                "type": "string",
                "description": "Patient ID to lookup appointments for"
            },
            "includeHistory": {
                "type": "boolean",
                "description": "Optional: Include past appointments (default: false, only upcoming)"
            },
            "sessionId": {
                "type": "string",
                "description": "Session identifier for tracking"
            }
        },
        "required": ["patientId", "sessionId"]
    })

    # ========== PROVIDER & LOCATION TOOLS (2) ==========

    # 13. Select Provider
    select_provider_schema = json.dumps({
        "type": "object",
        "properties": {
            "specialty": {
                "type": "string",
                "description": "Optional: Filter by specialty (primary_care, cardiology, dermatology, etc.)"
            },
            "locationId": {
                "type": "string",
                "description": "Optional: Filter by location ID"
            },
            "acceptingNewPatients": {
                "type": "boolean",
                "description": "Optional: Filter by accepting new patients (default: true)"
            },
            "sessionId": {
                "type": "string",
                "description": "Session identifier for tracking"
            }
        },
        "required": ["sessionId"]
    })

    # 14. Select Location
    select_location_schema = json.dumps({
        "type": "object",
        "properties": {
            "servicesOffered": {
                "type": "string",
                "description": "Optional: Filter by services (primary_care, imaging, lab, urgent_care)"
            },
            "city": {
                "type": "string",
                "description": "Optional: Filter by city"
            },
            "sessionId": {
                "type": "string",
                "description": "Session identifier for tracking"
            }
        },
        "required": ["sessionId"]
    })

    # ========== INSURANCE & REFERRAL TOOLS (2) ==========

    # 15. Check Insurance
    check_insurance_schema = json.dumps({
        "type": "object",
        "properties": {
            "patientId": {
                "type": "string",
                "description": "Patient ID (from verification)"
            },
            "providerId": {
                "type": "string",
                "description": "Optional: Provider ID to check coverage for"
            },
            "appointmentType": {
                "type": "string",
                "description": "Optional: Type of appointment to check coverage for"
            },
            "sessionId": {
                "type": "string",
                "description": "Session identifier for tracking"
            }
        },
        "required": ["patientId", "sessionId"]
    })

    # 16. Check Referral
    check_referral_schema = json.dumps({
        "type": "object",
        "properties": {
            "patientId": {
                "type": "string",
                "description": "Patient ID (from verification)"
            },
            "specialty": {
                "type": "string",
                "description": "Specialty to check referral requirement for (cardiology, neurology, orthopedics, etc.)"
            },
            "sessionId": {
                "type": "string",
                "description": "Session identifier for tracking"
            }
        },
        "required": ["patientId", "specialty", "sessionId"]
    })

    # ========== INTAKE TOOLS (3) ==========

    # 17. Start Intake
    start_intake_schema = json.dumps({
        "type": "object",
        "properties": {
            "patientId": {
                "type": "string",
                "description": "Optional: Patient ID if existing patient"
            },
            "firstName": {
                "type": "string",
                "description": "First name"
            },
            "lastName": {
                "type": "string",
                "description": "Last name"
            },
            "dateOfBirth": {
                "type": "string",
                "description": "Date of birth (YYYY-MM-DD)"
            },
            "sessionId": {
                "type": "string",
                "description": "Session identifier for tracking"
            }
        },
        "required": ["firstName", "lastName", "dateOfBirth", "sessionId"]
    })

    # 18. Collect Reason (Controlled Vocabulary Only)
    collect_reason_schema = json.dumps({
        "type": "object",
        "properties": {
            "intakeId": {
                "type": "string",
                "description": "Intake record ID from startIntakeTool"
            },
            "reasonCategory": {
                "type": "string",
                "description": "Category ONLY - NO medical details (annual_checkup, follow_up, new_concern, procedure, screening, wellness_visit, preventive_care)"
            },
            "specificReason": {
                "type": "string",
                "description": "Optional: Brief description (NO medical details, symptoms, or diagnoses)"
            },
            "sessionId": {
                "type": "string",
                "description": "Session identifier for tracking"
            }
        },
        "required": ["intakeId", "reasonCategory", "sessionId"]
    })

    # 19. Send Forms
    send_forms_schema = json.dumps({
        "type": "object",
        "properties": {
            "intakeId": {
                "type": "string",
                "description": "Intake record ID from startIntakeTool"
            },
            "patientId": {
                "type": "string",
                "description": "Patient ID"
            },
            "deliveryMethod": {
                "type": "string",
                "description": "Delivery method (email or sms)"
            },
            "sessionId": {
                "type": "string",
                "description": "Session identifier for tracking"
            }
        },
        "required": ["intakeId", "patientId", "sessionId"]
    })

    # ========== PREP INSTRUCTIONS TOOL (1) ==========

    # 20. Send Prep Instructions
    send_prep_instructions_schema = json.dumps({
        "type": "object",
        "properties": {
            "appointmentId": {
                "type": "string",
                "description": "Appointment ID to send prep instructions for"
            },
            "patientId": {
                "type": "string",
                "description": "Patient ID"
            },
            "sessionId": {
                "type": "string",
                "description": "Session identifier for tracking"
            }
        },
        "required": ["appointmentId", "patientId", "sessionId"]
    })

    # Return all tool schemas
    return [
        # Verification Tools (5)
        {
            "type": "tool",
            "name": TOOL_VERIFY_IDENTITY,
            "description": "Verify patient identity using name and date of birth (Level 1 verification). Required before any appointment scheduling.",
            "inputSchema": verify_identity_schema
        },
        {
            "type": "tool",
            "name": TOOL_VERIFY_PHONE,
            "description": "Verify patient phone number for additional security (Level 2 verification). Use after basic identity verification.",
            "inputSchema": verify_phone_schema
        },
        {
            "type": "tool",
            "name": TOOL_VERIFY_EMAIL,
            "description": "Verify patient email address for additional security (Level 2 verification). Use after basic identity verification.",
            "inputSchema": verify_email_schema
        },
        {
            "type": "tool",
            "name": TOOL_SETUP_PROXY,
            "description": "Setup proxy access for parent, legal guardian, caregiver, or authorized representative to act on behalf of patient. Auto-approves parents for minors.",
            "inputSchema": setup_proxy_schema
        },
        {
            "type": "tool",
            "name": TOOL_CAPTURE_CONSENT,
            "description": "Capture explicit patient consent before accessing protected health information (PHI). HIPAA required.",
            "inputSchema": capture_consent_schema
        },

        # Appointment Tools (7)
        {
            "type": "tool",
            "name": TOOL_SEARCH_AVAILABILITY,
            "description": "Search for available appointment slots by provider, location, specialty, date range, and time preference.",
            "inputSchema": search_availability_schema
        },
        {
            "type": "tool",
            "name": TOOL_HOLD_SLOT,
            "description": "Hold an appointment slot for 10 minutes to prevent double-booking while completing the scheduling process.",
            "inputSchema": hold_slot_schema
        },
        {
            "type": "tool",
            "name": TOOL_SCHEDULE_APPOINTMENT,
            "description": "Schedule an appointment using a held slot. Requires Level 1 verification (identity). Creates appointment and sends confirmation.",
            "inputSchema": schedule_appointment_schema
        },
        {
            "type": "tool",
            "name": TOOL_RESCHEDULE_APPOINTMENT,
            "description": "Reschedule an existing appointment to a new date/time. Requires Level 1 verification. Releases old slot and books new slot.",
            "inputSchema": reschedule_appointment_schema
        },
        {
            "type": "tool",
            "name": TOOL_CANCEL_APPOINTMENT,
            "description": "Cancel an existing appointment. Requires Level 1 verification. Releases slot for others to book.",
            "inputSchema": cancel_appointment_schema
        },
        {
            "type": "tool",
            "name": TOOL_CONFIRM_APPOINTMENT,
            "description": "Confirm an upcoming appointment. Updates appointment status to confirmed.",
            "inputSchema": confirm_appointment_schema
        },
        {
            "type": "tool",
            "name": TOOL_LOOKUP_APPOINTMENT,
            "description": "Lookup patient's appointments. Requires Level 1 verification. Returns upcoming appointments by default, or all history if requested.",
            "inputSchema": lookup_appointment_schema
        },

        # Provider & Location Tools (2)
        {
            "type": "tool",
            "name": TOOL_SELECT_PROVIDER,
            "description": "Search for healthcare providers by specialty, location, and whether accepting new patients. No PHI access required.",
            "inputSchema": select_provider_schema
        },
        {
            "type": "tool",
            "name": TOOL_SELECT_LOCATION,
            "description": "Search for clinic locations by services offered and city. No PHI access required.",
            "inputSchema": select_location_schema
        },

        # Insurance & Referral Tools (2)
        {
            "type": "tool",
            "name": TOOL_CHECK_INSURANCE,
            "description": "Check patient insurance coverage, copay amount, and pre-authorization requirements. Requires Level 1 verification. PHI access logged.",
            "inputSchema": check_insurance_schema
        },
        {
            "type": "tool",
            "name": TOOL_CHECK_REFERRAL,
            "description": "Check if specialty requires referral and if patient has active referral on file. Requires Level 1 verification. PHI access logged.",
            "inputSchema": check_referral_schema
        },

        # Intake Tools (3)
        {
            "type": "tool",
            "name": TOOL_START_INTAKE,
            "description": "Start patient intake process. Determines new vs existing patient and creates intake record with required forms list.",
            "inputSchema": start_intake_schema
        },
        {
            "type": "tool",
            "name": TOOL_COLLECT_REASON,
            "description": "Collect reason for visit using CONTROLLED VOCABULARY ONLY. DO NOT collect medical details, symptoms, or diagnoses. Categories only.",
            "inputSchema": collect_reason_schema
        },
        {
            "type": "tool",
            "name": TOOL_SEND_FORMS,
            "description": "Send patient intake forms via email or SMS. Generates secure portal link. PHI access logged.",
            "inputSchema": send_forms_schema
        },

        # Prep Instructions Tool (1)
        {
            "type": "tool",
            "name": TOOL_SEND_PREP_INSTRUCTIONS,
            "description": "Send appointment preparation instructions (what to bring, fasting requirements, arrival time). PHI access logged.",
            "inputSchema": send_prep_instructions_schema
        }
    ]
