# Healthcare Appointment Scheduling Agent

**HIPAA-Compliant Voice Assistant for Medical Appointment Scheduling**

A production-ready, HIPAA-compliant voice agent that handles healthcare appointment scheduling while maintaining strict privacy and security standards. This agent provides appointment management capabilities WITHOUT discussing medical details.

---

## 🏥 Overview

This healthcare voice agent is designed to handle appointment scheduling and administrative tasks while maintaining strict HIPAA compliance. It features:

- **20 specialized healthcare tools** covering verification, scheduling, insurance, intake, and prep
- **Multi-level identity verification** (Name+DOB, Phone, Email, MRN)
- **Proxy access support** for parents, caregivers, and authorized representatives
- **15-minute session timeout** with automatic security logout
- **Full PHI access audit logging** with tamper-proof hashing
- **Medical detail escalation** - automatically escalates clinical questions to staff
- **Slot hold + confirm pattern** to prevent double-booking

---

## 🚨 CRITICAL: HIPAA Compliance

### What This Agent CAN Do:
✅ Schedule, reschedule, and cancel appointments
✅ Verify patient identity (name, DOB, phone, email)
✅ Check insurance coverage and copay
✅ Verify referral requirements
✅ Send intake forms and prep instructions
✅ Provide administrative information (hours, parking, what to bring)

### What This Agent CANNOT Do:
❌ Discuss diagnoses, symptoms, or medical conditions
❌ Provide medical advice or treatment recommendations
❌ Discuss test results, lab work, or imaging
❌ Review medical records or treatment history
❌ Discuss medications or prescriptions

### Escalation Triggers
If a caller mentions these topics, the agent immediately escalates to clinical staff:
- `diagnosis`, `medication`, `prescription`, `test results`
- `medical records`, `treatment`, `symptoms`, `pain`
- `imaging`, `x-ray`, `MRI`, `CT scan`
- `lab results`, `biopsy`, `pathology`

---

## 📋 Architecture

```
Healthcare_Agent/
├── config/                      # Configuration
│   ├── constants.py            # All constants, table names, HIPAA settings
│   └── settings.py             # Environment-based config with HIPAA validation
├── security/                    # HIPAA Security (UNIQUE to Healthcare Agent)
│   ├── audit_logger.py         # PHI access logging with tamper detection
│   └── session_manager.py      # Session timeout and isolation
├── tools/                       # 20 HIPAA-Compliant Tools
│   ├── verification_tools.py   # 5 tools: Identity, Phone, Email, Proxy, Consent
│   ├── appointment_tools.py    # 7 tools: Search, Hold, Schedule, Reschedule, Cancel, Confirm, Lookup
│   ├── provider_tools.py       # 2 tools: Select Provider, Select Location
│   ├── insurance_tools.py      # 2 tools: Check Insurance, Check Referral
│   ├── intake_tools.py         # 3 tools: Start Intake, Collect Reason, Send Forms
│   └── prep_tools.py           # 1 tool: Send Prep Instructions
├── core/                        # Business Logic
│   └── tool_processor.py       # Processes all 20 tools with escalation checking
├── prompts/                     # System Prompts
│   └── healthcare_system_prompt.py  # HIPAA-compliant prompt with escalation rules
├── streaming/                   # Bedrock Streaming
│   ├── bedrock_manager.py      # Bidirectional streaming with Bedrock
│   ├── audio_streamer.py       # Audio I/O management
│   └── tool_schemas.py         # Schema definitions for all 20 tools
├── utils/                       # Utilities
│   ├── logging.py              # Logging utilities
│   └── timing.py               # Performance timing
└── healthcare_agent.py          # Main entry point
```

---

## 🛠️ Tools (20 Total)

### Verification Tools (5)
| Tool | Description | Verification Level |
|------|-------------|-------------------|
| `verifyIdentityTool` | Verify name + DOB | Level 1 (Light) |
| `verifyPhoneTool` | Verify phone number | Level 2 (Standard) |
| `verifyEmailTool` | Verify email address | Level 2 (Standard) |
| `setupProxyTool` | Setup proxy access (parent, caregiver) | Level 1 + Proxy |
| `captureConsentTool` | Capture explicit consent (HIPAA required) | N/A |

### Appointment Tools (7)
| Tool | Description | Requires Verification |
|------|-------------|----------------------|
| `searchAvailabilityTool` | Search available slots | No |
| `holdSlotTool` | Hold slot for 10 minutes | No |
| `scheduleAppointmentTool` | Schedule appointment | Level 1 |
| `rescheduleAppointmentTool` | Reschedule existing appointment | Level 1 |
| `cancelAppointmentTool` | Cancel appointment | Level 1 |
| `confirmAppointmentTool` | Confirm appointment | No |
| `lookupAppointmentTool` | Lookup patient appointments | Level 1 |

### Provider & Location Tools (2)
| Tool | Description | Requires Verification |
|------|-------------|----------------------|
| `selectProviderTool` | Search providers by specialty | No |
| `selectLocationTool` | Search clinic locations | No |

### Insurance & Referral Tools (2)
| Tool | Description | Requires Verification |
|------|-------------|----------------------|
| `checkInsuranceTool` | Check coverage and copay | Level 1 |
| `checkReferralTool` | Check referral requirements | Level 1 |

### Intake Tools (3)
| Tool | Description | Requires Verification |
|------|-------------|----------------------|
| `startIntakeTool` | Start patient intake | No |
| `collectReasonTool` | Collect reason (controlled vocabulary) | No |
| `sendFormsTool` | Send intake forms via email/SMS | No |

### Prep Tools (1)
| Tool | Description | Requires Verification |
|------|-------------|----------------------|
| `sendPrepInstructionsTool` | Send prep instructions | No |

---

## 🔐 Security Features

### 1. Identity Verification (3 Levels)
- **Level 0 (None)**: Public information only
- **Level 1 (Light)**: Name + DOB → Sufficient for scheduling
- **Level 2 (Standard)**: Level 1 + Phone/Email → For sensitive data
- **Level 3 (Full)**: Level 2 + MRN/Patient ID → Medical records (not used by this agent)

### 2. Session Management
- **15-minute timeout**: Auto-logout after inactivity
- **13-minute warning**: Alert user before timeout
- **Session isolation**: No data persists between sessions
- **Secure termination**: Clean session cleanup with audit log

### 3. Audit Logging
Every PHI access is logged with:
- **Who**: User ID / Patient ID
- **When**: Timestamp (UTC)
- **What**: Resource type and ID
- **Why**: Reason for access
- **How**: Action performed (READ, UPDATE, DELETE)
- **Tamper detection**: SHA-256 hash for integrity
- **Retention**: 6 years (HIPAA requirement)

### 4. Minimum Necessary Principle
Tools only access the minimum data required:
- Scheduling tools: Name, DOB, contact info
- Insurance tools: Coverage status, copay
- Intake tools: General categories only (NO medical details)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- AWS Account with Bedrock access
- PyAudio for voice I/O
- DynamoDB tables created

### Installation

```bash
# Navigate to Healthcare Agent directory
cd Healthcare_Agent

# Install dependencies
pip install -r requirements.txt

# Set AWS credentials (via environment variables or ~/.aws/credentials)
export AWS_ACCESS_KEY_ID="your_access_key"
export AWS_SECRET_ACCESS_KEY="your_secret_key"
export AWS_DEFAULT_REGION="us-east-1"

# Create DynamoDB tables (see DynamoDB Setup below)
python setup_tables.py  # (You'll need to create this)
```

### Running the Agent

```bash
# Normal mode (production)
python healthcare_agent.py

# Debug mode (development only - HIPAA warning)
python healthcare_agent.py --debug
```

---

## 📊 DynamoDB Tables (10 Required)

| Table Name | Primary Key | Purpose |
|------------|-------------|---------|
| `Healthcare_Patients` | `patientId` | Patient demographics and contact info |
| `Healthcare_Appointments` | `appointmentId` | Scheduled appointments |
| `Healthcare_Providers` | `providerId` | Healthcare providers directory |
| `Healthcare_Locations` | `locationId` | Clinic locations |
| `Healthcare_Availability` | `slotId` | Available appointment slots |
| `Healthcare_Insurance` | `insuranceId` | Insurance coverage information |
| `Healthcare_Referrals` | `referralId` | Referral records |
| `Healthcare_Intake_Forms` | `intakeId` | Patient intake records |
| `Healthcare_Audit_Logs` | `auditLogId` | PHI access audit trail |
| `Healthcare_Sessions` | `sessionId` | Active sessions with timeout |

---

## 💬 Example Conversation Flow

### Scenario: New Appointment

```
Agent: "Hello! I'm your healthcare appointment assistant. To help you today,
        I'll need to verify your identity. May I have your full name and
        date of birth?"

User:  "John Smith, January 15, 1980."

Agent: [Uses verifyIdentityTool]
       "Thank you, Mr. Smith. To schedule your appointment, I'll need to
        access your patient record. Do I have your consent to proceed?"

User:  "Yes."

Agent: [Uses captureConsentTool]
       "Great. What type of appointment do you need - annual checkup,
        follow-up, or a new concern?"

User:  "Annual checkup."

Agent: [Uses collectReasonTool with reasonCategory: "annual_checkup"]
       "Do you have a provider preference, or would you like to see the
        next available doctor?"

User:  "Dr. Johnson."

Agent: [Uses searchAvailabilityTool with providerId]
       "I found an opening on March 15th at 2:00 PM with Dr. Johnson.
        Let me hold that slot for you."
       [Uses holdSlotTool]
       "Let me verify your insurance coverage."
       [Uses checkInsuranceTool]
       "Your insurance shows a copay of $25. Shall I schedule this appointment?"

User:  "Yes, please."

Agent: [Uses scheduleAppointmentTool]
       "Perfect! I've scheduled your appointment for March 15th at 2:00 PM
        with Dr. Johnson at Main Street Clinic. Your confirmation number
        is APPT-20260315-ABC123."
       [Uses sendPrepInstructionsTool]
       "I'll send you preparation instructions and what to bring to your email."
```

### Scenario: Medical Question (Escalation)

```
User:  "I've been having these terrible headaches and dizziness, and I'm
        worried about my blood pressure medication..."

Agent: "I understand you have questions about your symptoms and medication,
        but I'm not able to discuss medical details. Let me connect you
        with our clinical staff who can help you with that. Would you
        like me to transfer you now, or would you prefer to have a nurse
        call you back?"
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Required
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1

# Optional
HEALTHCARE_DEBUG_MODE=false           # Never true in production!
HEALTHCARE_MODEL_ID=amazon.nova-sonic-v1:0
HEALTHCARE_SESSION_TIMEOUT=15         # Minutes
```

### HIPAA Compliance Validation

On startup, the agent validates:
- ✅ Audit logging is enabled
- ✅ Encryption at rest enabled
- ✅ Encryption in transit enabled
- ✅ Debug mode disabled (production)

If any validation fails, the agent will NOT start.

---

## 📝 Audit Logging Example

```python
{
  "auditLogId": "AUDIT-20260128143052-abc123",
  "timestamp": "2026-01-28T14:30:52.123456Z",
  "eventType": "PHI_ACCESS",
  "userId": "PAT-100001",
  "sessionId": "SES-xyz789",
  "action": "READ",
  "resourceType": "PATIENT",
  "resourceId": "PAT-100001",
  "phiAccessed": true,
  "success": true,
  "ipAddress": "192.168.1.100",
  "details": {
    "reason": "Identity verification for appointment scheduling",
    "minimum_necessary": true
  },
  "tamperHash": "a3f8b2...",
  "retentionDate": "2032-01-28T14:30:52.123456Z"  // 6 years
}
```

---

## ⚠️ Important Notes

### Production Deployment Checklist
- [ ] Debug mode DISABLED
- [ ] All 10 DynamoDB tables created and encrypted at rest
- [ ] AWS credentials use IAM roles (not hardcoded)
- [ ] TLS/SSL enabled for all connections
- [ ] Audit logs have backup/retention policy (6 years)
- [ ] Session timeout set to 15 minutes or less
- [ ] Escalation keywords monitored
- [ ] Staff escalation process tested
- [ ] HIPAA training completed for operators

### Known Limitations
1. **Voice-only interface**: No visual confirmation of PHI
2. **Controlled vocabulary for reason**: Cannot collect detailed medical history
3. **No medical advice**: All clinical questions escalated
4. **Session timeout**: Long calls may require re-verification
5. **Proxy verification**: Relies on honor system for relationship claims

---

## 🔄 Comparison to Other Agents

| Feature | Healthcare Agent | Banking Agent | Retail Agent | Hotel Agent |
|---------|-----------------|---------------|--------------|-------------|
| **Security Module** | ✅ Yes (HIPAA) | ✅ Yes (PCI-DSS) | ❌ No | ❌ No |
| **Session Timeout** | 15 min | 10 min | N/A | N/A |
| **Audit Logging** | Full PHI access | Transaction logs | Basic | Basic |
| **Identity Verification** | 3 levels | 2FA + PIN | Barcode scan | Reservation # |
| **Escalation Rules** | Medical details | Fraud/disputes | Manager | Front desk |
| **Proxy Access** | ✅ Yes | ❌ No | ❌ No | ✅ Yes (group bookings) |
| **Tool Count** | 20 | 15 | 12 | 14 |

**Unique to Healthcare Agent:**
- `security/` module with `AuditLogger` and `SessionManager`
- Escalation keyword monitoring
- Controlled vocabulary for reason collection
- Proxy access for minors and authorized representatives
- 6-year audit retention

---

## 📞 Support

For questions or issues:
1. Check this README and IMPLEMENTATION_PLAN.md
2. Review HIPAA compliance checklist
3. Check audit logs for PHI access patterns
4. Contact your HIPAA compliance officer

---

## 📄 License

Internal use only. HIPAA-compliant healthcare data handling required.

---

## 🎯 Next Steps

1. **Create DynamoDB tables** with sample data
2. **Test all 20 tools** individually
3. **Test appointment workflow** end-to-end
4. **Test escalation scenarios** (medical keywords)
5. **Test session timeout** (15 min + warning at 13 min)
6. **Review audit logs** for PHI access patterns
7. **HIPAA compliance review** with legal/compliance team
8. **Staff training** on escalation handling

---

**Built with HIPAA compliance from the ground up. Patient privacy is our top priority.**
