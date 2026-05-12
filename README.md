# Voice Agents Master - Project Summary

## Overview

Voice Agents with AWS Bedrock Nova Sonic is a collection of ready-to-run AI voice agents that let you have natural, spoken conversations with an intelligent assistant. Just like if you were to call a real business and talk to a representative

Each agent is built for a specific industry and handles real tasks: checking reservations, processing returns, answering banking questions, and taking restaurant orders. You speak, the agent listens and responds in real time, and it takes action by looking up or updating data on your behalf

The repo currently includes five agents:
1. Hotel: Front desk assistnat that manages guest reservations and requests
2. Restaurant: Handles reservations, waitlists, and food orders
3. Retail Kiosk: Self-service customer support for returns, transactions, and changes in membership
4. Call Center: Inbound phone support for store hours, inventory, and appointments
5. Banking: Secure voice banking with multi-step authentication and account services

All the agents are built on AWS Bedrock Nova Sonic with real-time audio streaming, low-latency responses, and the ability to interrupt the agent mid-sentence. Each one connects to a database and can actually read and write data during the conversation

## Project Structure

```
voice-agents-master/
├── Hotel_Agent/                    # Virtual hotel receptionist
│   ├── hotel_agent.py              # Main agent implementation
│   ├── db_setup.py                 # DynamoDB setup for hotel data
│   ├── app.py                      # Streamlit dashboard
│   └── requirements.txt            # Dependencies
│
├── Customer_Service_Agent/         # Retail member service kiosk
│   ├── retail_agent.py             # Main agent implementation
│   ├── db_setup.py                 # DynamoDB setup for retail data
│   ├── app.py                      # Streamlit dashboard
│   ├── requirements.txt            # Dependencies
│   └── README.md                   # Detailed documentation
│
├── Club_Call_Center_Agent/         # Inbound call center
│   ├── call_center_agent.py        # Main agent implementation
│   ├── db_setup.py                 # DynamoDB setup for call center data
│   ├── app.py                      # Streamlit dashboard
│   ├── requirements.txt            # Dependencies
│   ├── README.md                   # Detailed documentation
│   └── IMPLEMENTATION_NOTES.md     # Implementation guide
│
├── Restaurant_Agent/               # Restaurant reservations & ordering
│   ├── restaurant_agent.py         # Main agent implementation
│   ├── db_setup.py                 # DynamoDB setup for restaurant data
│   ├── app.py                      # Streamlit dashboard
│   ├── requirements.txt            # Dependencies
│   └── README.md                   # Detailed documentation
│
├── Banking_Agent/                  # Secure voice banking customer service
│   ├── banking_agent.py            # Main agent implementation (2,596 lines)
│   ├── db_setup.py                 # DynamoDB setup for banking data
│   ├── banking_dashboard.py        # Streamlit monitoring dashboard
│   ├── requirements.txt            # Dependencies
│   └── README.md                   # Comprehensive documentation
│
├── PROJECT_SUMMARY.md              # This file
├── PROJECT_STATUS.md               # Detailed status report
├── AGENT_COMPARISON.md             # Comparison of all agents
└── QUICK_START.md                  # 10-minute setup guide
```

## Agents

### 1. Hotel Agent 🏨
**Use Case:** Virtual front desk assistant for hotels

**Capabilities:**
- Guest identity verification (name + DOB)
- Reservation lookup and status checking
- Room type modifications
- Special request management
- Balance inquiries

**Tools:** 3 tools
- `checkGuestProfileTool` - Identity verification
- `checkReservationStatusTool` - Reservation queries
- `updateReservationTool` - Modify bookings

**Database:** 2 tables (Hotel_Guests, Hotel_Reservations)

**Status:** ✅ Complete 

---

### 2. Customer Service Agent 🛒
**Use Case:** Self-service kiosk for membership warehouse clubs (Costco/Sam's Club style)

**Capabilities:**
- Barcode-based member verification
- Return processing with computer vision verification
- Transaction issue resolution (double-scans, missed items)
- Membership management (contact info, household members)
- Complaint logging with tracking

**Tools:** 9 tools
- `verifyMemberTool` - Barcode scan verification
- `lookupTransactionTool` - Find transactions
- `modifyMembershipTool` - Update member info
- `addHouseholdMemberTool` - Add household member
- `removeHouseholdMemberTool` - Remove household member
- `verifyReturnItemTool` - CV-based item verification
- `initiateReturnTool` - Process returns
- `processTransactionIssueTool` - Handle checkout errors
- `fileComplaintTool` - Log complaints

**Database:** 4 tables (Retail_Members, Retail_Transactions, Retail_Returns, Retail_Service_Requests)

**Status:** ✅ Complete (1,620 lines of code)

**Key Innovation:** Computer vision integration for fraud-resistant returns

---

### 3. Call Center Agent ☎️
**Use Case:** Inbound call handling for retail warehouse club

**Capabilities:**
- Member verification by phone number or member ID
- Store hours queries (regular, holiday, department-specific)
- Inventory availability checks with aisle locations
- Curbside order status tracking
- Appointment scheduling (Tire, Optical, Hearing, Pharmacy)
- Specialty order tracking (cakes, custom items)
- New cake order placement (48-hour lead time)

**Tools:** 8 tools
- `verifyMemberTool` - Verify caller identity
- `checkStoreHoursTool` - Hours queries
- `checkInventoryTool` - Product availability
- `checkCurbsideOrderTool` - Order status
- `scheduleAppointmentTool` - Book appointments
- `checkSpecialtyOrderTool` - Check cake orders
- `createCakeOrderTool` - Place new cake orders
- `checkAppointmentTool` - Verify appointments

**Database:** 6 tables (Store_Info, Inventory, Curbside_Orders, Appointments, Specialty_Orders, Members)

**Status:** ✅ Complete

**Key Innovation:** Phone-optimized conversational flow with clear verbal confirmations

---

### 4. Restaurant Agent 🍝
**Use Case:** Full-service restaurant reservation and food ordering system

**Capabilities:**
- Reservation management (create, edit, cancel, confirm)
- Phone number-first lookup (handles "I forgot the name" cases)
- Waitlist management (walk-in + reservation waitlist)
- Current wait time quotes
- Auto-notify when table is ready
- Party metadata capture (size, high chair, accessibility, seating preference)
- Guest seating from reservations or waitlist
- Food ordering for seated guests
- Menu viewing by category
- Order status tracking

**Tools:** 12 tools
- `lookupReservationTool` - Find by phone/name/ID (phone priority!)
- `createReservationTool` - New reservation with metadata
- `editReservationTool` - Modify reservation details
- `cancelReservationTool` - Cancel reservation
- `confirmReservationTool` - Verify reservation details
- `joinWaitlistTool` - Add to walk-in or reservation waitlist
- `checkWaitTimeTool` - Quote current wait time
- `notifyTableReadyTool` - Send table-ready notification
- `seatGuestTool` - Mark guest as seated
- `placeOrderTool` - Take food order
- `viewMenuTool` - Show menu items
- `checkOrderStatusTool` - Check order status

**Database:** 7 tables (Reservations, Waitlist, Tables, Customers, Orders, Menu, Notifications)

**Status:** ✅ Complete

**Key Innovation:** Dual waitlist system + phone number-first identity resolution + integrated food ordering

---

### 5. Banking Agent 🏦
**Use Case:** Secure voice banking customer service with multi-factor authentication

**Capabilities:**
- Multi-factor authentication (Phone → OTP → Security Question)
- Progressive authentication (3 levels based on operational risk)
- Account information (balances, transactions, statements)
- Card services (lost/stolen, freeze/unfreeze, disputes)
- Payments & transfers (internal, Zelle, bill pay, stop payment)
- Fraud reporting with immediate card deactivation
- Dispute management with Regulation E compliance
- Provisional credit tracking

**Tools:** 21 tools
- **Authentication (3):** `authenticateTool`, `verifyOtpTool`, `stepUpAuthenticationTool`
- **Account Info (4):** `checkBalanceTool`, `viewRecentTransactionsTool`, `searchTransactionsTool`, `requestStatementTool`
- **Card Services (6):** `reportLostCardTool`, `freezeCardTool`, `unfreezeCardTool`, `checkReplacementStatusTool`, `disputeChargeTool`, `clarifyMerchantTool`
- **Payments (5):** `internalTransferTool`, `checkZelleStatusTool`, `setupBillpayTool`, `stopPaymentTool`, `explainPendingTool`
- **Fraud (3):** `reportFraudTool`, `checkDisputeStatusTool`, `explainProvisionalCreditTool`

**Database:** 10 tables (Customers, Accounts, Transactions, Cards, Disputes, Transfers, AuthSessions, AuditLogs, Consents, BillPay)

**Status:** ✅ Complete

**Key Innovation:** Progressive authentication system with Level 1/2/3 security, immutable audit trail, full Regulation E compliance, jurisdiction-aware consent recording

**Security Features:**
- SHA-256 hashed security questions
- 6-digit OTP with 5-minute expiry
- 30-minute session timeout with activity extension
- PII access tracking
- Step-up authentication for high-risk operations
- Zero liability fraud protection

---

## Shared Architecture

All agents share the same core architecture as the original hotel agent:

### Core Components

1. **BedrockStreamManager**
   - Manages HTTP/2 bidirectional streaming with AWS Bedrock
   - Handles session initialization, audio I/O, and tool execution
   - Supports real-time barge-in (interrupt agent mid-sentence)

2. **ToolProcessor** (domain-specific)
   - Async tool execution with DynamoDB integration
   - Custom implementation per agent
   - Non-blocking design for real-time responsiveness

3. **AudioStreamer**
   - PyAudio-based audio capture and playback
   - Separate input/output streams for full-duplex
   - 16kHz input, 24kHz output

4. **Streamlit Dashboard**
   - Real-time conversation monitoring
   - Tool execution tracking
   - Token usage analytics
   - Auto-refresh every 3 seconds

### Technical Stack
- **AI Model:** AWS Bedrock Nova Sonic (amazon.nova-sonic-v1:0)
- **Database:** AWS DynamoDB
- **Audio:** PyAudio (16-bit PCM)
- **Framework:** Python asyncio
- **Dashboard:** Streamlit
- **Region:** us-east-1

### Key Features
- ✅ HTTP/2 Bidirectional Streaming
- ✅ Real-time barge-in support
- ✅ Async tool execution
- ✅ Low-latency responses (<500ms typical)
- ✅ Natural voice conversations
- ✅ Tool/function calling
- ✅ DynamoDB integration
- ✅ Live monitoring dashboard

---

## Getting Started

### Prerequisites
- Python 3.8+
- AWS account with Bedrock access (Nova Sonic enabled in us-east-1)
- AWS credentials configured
- Microphone and speakers

### Quick Start

#### Hotel Agent
```bash
cd Hotel_Agent
pip install -r requirements.txt
python db_setup.py
# Edit hotel_agent.py to add AWS credentials
python hotel_agent.py
```

#### Customer Service Agent
```bash
cd Customer_Service_Agent
pip install -r requirements.txt
python db_setup.py
# Edit retail_agent.py to add AWS credentials
python retail_agent.py
```

#### Call Center Agent
```bash
cd Club_Call_Center_Agent
pip install -r requirements.txt
python db_setup.py
# Edit call_center_agent.py to add AWS credentials
python call_center_agent.py
```

#### Restaurant Agent
```bash
cd Restaurant_Agent
pip install -r requirements.txt
python db_setup.py
# Edit restaurant_agent.py to add AWS credentials
python restaurant_agent.py
```

#### Banking Agent
```bash
cd Banking_Agent
pip install -r requirements.txt
python db_setup.py
# Edit banking_agent.py to add AWS credentials (line 2590)
python banking_agent.py
```

### Launch Dashboard (Optional)
```bash
# In separate terminal
# For Hotel/Customer Service/Call Center/Restaurant agents:
streamlit run app.py

# For Banking Agent:
streamlit run banking_dashboard.py
```

---

## Architecture Patterns

### Adding New Agents

To create a new voice agent (e.g., healthcare, restaurant, etc.):

1. **Copy Base Structure**
   ```bash
   cp -r Customer_Service_Agent/ New_Agent/
   ```

2. **Define Database Schema**
   - Design DynamoDB tables for your domain
   - Update `db_setup.py` with new tables
   - Seed with sample data

3. **Create Tools**
   - Define tool schemas in `start_prompt()`
   - Implement tool handlers in ToolProcessor
   - Add routing in `_run_tool()`

4. **Customize System Prompt**
   - Update personality and tone
   - Define conversation flows
   - Add domain-specific policies

5. **Update Dashboard**
   - Customize UI colors/branding
   - Add domain-specific metrics
   - Modify event rendering

### Tool Design Principles

1. **Verification First** - Always verify identity before sensitive operations
2. **Async Execution** - Use async/await for non-blocking tool calls
3. **Clear Feedback** - Return detailed messages for the agent to convey
4. **Error Handling** - Return structured errors for graceful degradation
5. **Decimal Handling** - Convert Decimal to string for JSON serialization

### System Prompt Best Practices

1. **Security Protocol** - Clear identity verification requirements
2. **Step-by-Step Flows** - Explicit instructions for multi-step processes
3. **Personality Definition** - Warm, professional, empathetic tone
4. **Policy Clarity** - Transparent about limitations and timelines
5. **Conciseness** - Voice-optimized (shorter responses than text)

---

## Production Considerations

### Security
- [ ] Encrypt member/guest data at rest
- [ ] Implement session timeouts
- [ ] Add fraud detection for high-risk operations
- [ ] Audit logging for compliance
- [ ] Rotate AWS credentials regularly

### Scalability
- [ ] DynamoDB auto-scaling
- [ ] Connection pooling for the database
- [ ] Redis caching for hot data
- [ ] Deploy to ECS/Lambda
- [ ] Load balancing for multiple kiosks

### Monitoring
- [ ] CloudWatch metrics for latency
- [ ] Alert on failed tool executions
- [ ] Track conversation success rates
- [ ] Monitor barge-in frequency
- [ ] Dashboard for operations team

### Quality Assurance
- [ ] End-to-end testing suite
- [ ] A/B testing for system prompts
- [ ] User satisfaction surveys
- [ ] Conversation analysis for improvements
- [ ] Regression testing for tool changes

---

## Resources

### Documentation
- [AWS Bedrock Nova Sonic Docs](https://docs.aws.amazon.com/bedrock/)
- [PyAudio Documentation](https://people.csail.mit.edu/hubert/pyaudio/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [DynamoDB Developer Guide](https://docs.aws.amazon.com/dynamodb/)
