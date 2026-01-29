# Club Call Center Agent ☎️

A real-time voice AI agent for handling inbound calls to a retail warehouse club. Built with AWS Bedrock Nova Sonic for natural phone conversations with members calling about hours, inventory, orders, and appointments.

## Overview

This agent handles the most common reasons members call the store:
- ✅ Store hours (regular, holiday, severe weather)
- ✅ Item availability and location
- ✅ Curbside order status
- ✅ Tire/Optical/Hearing/Pharmacy appointments
- ✅ Specialty orders (cakes, custom items)

## Features

### Core Capabilities
- **Member Verification** - By phone number or member ID
- **Store Hours Queries** - Regular, holiday, department-specific
- **Inventory Checks** - Real-time stock levels and aisle locations
- **Curbside Order Status** - Track online orders for pickup
- **Appointment Scheduling** - Book Tire, Optical, Hearing Aid, Pharmacy
- **Specialty Order Tracking** - Check cake and custom order status
- **Cake Ordering** - Place new cake orders with 48-hour lead time

### Technical Features
- ✅ HTTP/2 Bidirectional Audio Streaming
- ✅ Real-time barge-in support (natural phone interruptions)
- ✅ 8 specialized tools for call center operations
- ✅ DynamoDB backend (6 tables)
- ✅ Streamlit dashboard for call monitoring
- ✅ Natural phone conversation flow

## Architecture

###Database Schema (Dyn amoDB)

**CallCenter_Store_Info:**
- Store hours (regular + holiday)
- Department information (Tire, Optical, Hearing, Pharmacy, Bakery)
- Special closures (weather, events)

**CallCenter_Inventory:**
- Product availability
- Stock levels
- Aisle locations
- Pricing

**CallCenter_Curbside_Orders:**
- Online order status
- Pickup instructions
- Ready times

**CallCenter_Appointments:**
- Scheduled appointments by department
- Confirmation numbers
- Service types

**CallCenter_Specialty_Orders:**
- Cake orders
- Custom requests
- Pickup schedules

**CallCenter_Members:**
- Basic member info for verification

### Tools (8 Total)

| Tool | Purpose |
|------|---------|
| `verifyMemberTool` | Verify caller by phone or member ID |
| `checkStoreHoursTool` | Hours queries (regular/holiday/department) |
| `checkInventoryTool` | Item availability and location |
| `checkCurbsideOrderTool` | Curbside order status |
| `scheduleAppointmentTool` | Book appointments |
| `checkSpecialtyOrderTool` | Check cake/custom orders |
| `createCakeOrderTool` | Place new cake order |
| `checkAppointmentTool` | Verify existing appointments |

## Setup Instructions

### 1. Install Dependencies
```bash
cd Club_Call_Center_Agent
pip install -r requirements.txt
```

### 2. Setup Database
```bash
python db_setup.py
```

This creates 6 tables and seeds with:
- Store STORE-4523 (Denver) with full hours
- 5 sample inventory items
- 3 curbside orders (various statuses)
- 3 appointments (Tire, Optical, Pharmacy)
- 2 cake orders
- 3 test members

### 3. Configure AWS Credentials
Edit `call_center_agent.py` (lines at bottom):
```python
os.environ["AWS_ACCESS_KEY_ID"] = "your_key"
os.environ["AWS_SECRET_ACCESS_KEY"] = "your_secret"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
```

### 4. Run the Agent
```bash
python call_center_agent.py
```

### 5. Dashboard (Optional)
```bash
streamlit run app.py
```

## Usage Examples

### Example 1: Check Store Hours
**Caller:** "What time do you close today?"
**Agent:** "Today is Monday, we're open 9:00 AM to 9:00 PM. Can I help you with anything else?"

**Caller:** "What about Thanksgiving?"
**Agent:** *[Calls checkStoreHoursTool with queryType='holiday']* "We're CLOSED on Thanksgiving. We'll reopen the day after with regular hours."

### Example 2: Check Inventory
**Caller:** "Do you have the Samsung 65-inch TV in stock?"
**Agent:** *[Calls checkInventoryTool with productName='Samsung TV']* "Yes! The Samsung 65" 4K Smart TV is in stock. We have 8 available in the Electronics Department on the TV Wall. Price is $799.99."

**Caller:** "How about the Dyson vacuum?"
**Agent:** *[Checks inventory]* "The Dyson V15 Cordless Vacuum is currently out of stock. Expected restock in 5 days on February 1st."

### Example 3: Curbside Order Status
**Caller:** "Is my curbside order ready?"
**Agent:** "Let me check that for you. Can I get your phone number or member ID?"
**Caller:** "555-234-5678"
**Agent:** *[Verifies member, checks curbside order]* "Hi Sarah! Your order CURB-20260127-001 is ready for pickup! Park in designated curbside spots 1-10 and call when you arrive. Ready since 11:45 AM."

### Example 4: Schedule Appointment
**Caller:** "I need to schedule a tire installation"
**Agent:** "I'd be happy to help schedule that! What date works best for you?"
**Caller:** "Next Wednesday, February 3rd, around 3 PM"
**Agent:** *[Calls scheduleAppointmentTool]* "Perfect! I've scheduled your tire installation for February 3rd at 3:00 PM at our Tire Center. Your confirmation number is TIRE-54321."

### Example 5: Check Cake Order
**Caller:** "I ordered a birthday cake, is it ready?"
**Agent:** "Let me check on that for you. What's your member ID or the confirmation number?"
**Caller:** "Confirmation CAKE-78901"
**Agent:** *[Checks specialty order]* "Your Half Sheet chocolate cake with 'Happy Birthday Emma' is ready for pickup tomorrow at 2:00 PM!"

## Conversation Flow

### Standard Call Flow
1. **Greeting** → "Thank you for calling Denver Warehouse Club, how can I help you?"
2. **Member Verification** (if needed) → "May I have your phone number or member ID?"
3. **Need Assessment** → Listen to request
4. **Tool Execution** → Call appropriate tool(s)
5. **Information Delivery** → Provide clear, concise answer
6. **Follow-up** → "Is there anything else I can help you with?"
7. **Closing** → "Thank you for calling, have a great day!"

### Multi-Query Handling
Agent can handle multiple questions in one call:
- Hours + inventory check
- Curbside status + schedule appointment
- Multiple inventory items

## Key Policies & Rules

### Store Hours
- Regular hours: Mon-Fri 9AM-9PM, Sat 9AM-7PM, Sun 10AM-6PM
- Closed: Thanksgiving, Christmas
- Modified hours: Major holidays

### Departments
- **Tire Center:** Mon-Sat with appointments
- **Optical:** Mon-Sat, closed Sunday
- **Hearing Aid:** Mon-Sat limited hours
- **Pharmacy:** 7 days/week
- **Bakery:** 7 days/week for orders

### Cake Orders
- 48-hour minimum lead time
- Sizes: Quarter ($24.99), Half ($34.99), Full ($54.99)
- Custom inscriptions and decorations available

### Curbside Orders
- Track by order ID or member ID
- Statuses: Scheduled → Being Prepared → Ready for Pickup
- Pickup in designated spots 1-10

## Testing Scenarios

### Test 1: Hours Query
- **Ask:** "What are your holiday hours?"
- **Expected:** Agent provides full holiday schedule

### Test 2: Inventory - In Stock
- **Ask:** "Do you have rotisserie chicken?"
- **Expected:** "Yes, we have 45 available in the Deli Section"

### Test 3: Inventory - Out of Stock
- **Ask:** "Is the Dyson vacuum available?"
- **Expected:** "Out of stock, expected restock Feb 1st"

### Test 4: Curbside Order Ready
- **Member:** MEM-100001
- **Order:** CURB-20260127-001
- **Expected:** "Your order is ready for pickup!"

### Test 5: Schedule Appointment
- **Request:** Tire installation next week
- **Expected:** Appointment created with confirmation number

### Test 6: Cake Order Status
- **Confirmation:** CAKE-78901
- **Expected:** "Ready for pickup tomorrow at 2 PM"

## Dashboard Features

The Streamlit dashboard provides:
- Real-time call monitoring
- Tool execution tracking
- Inventory availability overview
- Today's appointments
- Pending curbside orders
- Call volume metrics

## Customization

### Adding New Departments
1. Update Store_Info table with department details
2. Add department-specific hours
3. Enable appointment booking if needed

### Adding New Product Categories
1. Add items to Inventory table
2. Include stock levels and locations
3. Set restock dates for out-of-stock items

### Modifying System Prompt
Edit `call_center_agent.py` system prompt to:
- Change personality/tone
- Add new policies
- Update department info
- Modify conversation flows

## Production Considerations

### Call Routing
- Integrate with phone system (Twilio, Amazon Connect)
- Route to voice agent or transfer to human
- Handle high call volumes with queue

### Data Integration
- Real-time inventory sync from POS
- Curbside order updates from online system
- Appointment calendar integration
- Cake order system connection

### Monitoring
- Track call resolution rates
- Monitor average handle time
- Alert on failed tool executions
- Dashboard for operations team

### Quality Assurance
- Call recording and analysis
- Sentiment tracking
- Escalation to human agents
- Continuous improvement based on feedback

## Differences from Customer Service Agent

| Feature | Customer Service Agent | Call Center Agent |
|---------|----------------------|-------------------|
| **Channel** | Self-service kiosk | Inbound phone calls |
| **Verification** | Barcode scan | Phone number/Member ID |
| **Primary Use** | Returns, transaction fixes | Information, appointments |
| **Interaction** | Visual + voice | Voice only |
| **Tools** | 9 (includes CV returns) | 8 (info-focused) |
| **Tone** | Efficient, action-oriented | Helpful, conversational |
| **Average Duration** | 1-2 min | 2-4 min |

## File Structure
```
Club_Call_Center_Agent/
├── call_center_agent.py      # Main agent (to be completed)
├── db_setup.py                # DynamoDB setup
├── app.py                     # Streamlit dashboard (to be created)
├── requirements.txt           # Dependencies (to be created)
└── README.md                 # This file
```

## Implementation Status

✅ Database schema designed (6 tables)
✅ Sample data seeded
✅ 8 tools implemented
✅ Tool processor complete
✅ README documentation

⏳ BedrockStreamManager (copy from Customer Service Agent)
⏳ AudioStreamer (copy from Customer Service Agent)
⏳ System prompt (phone-specific personality)
⏳ Streamlit dashboard
⏳ Requirements.txt

## Next Steps

To complete this agent:

1. **Copy Streaming Infrastructure** from Customer_Service_Agent/retail_agent.py:
   - BedrockStreamManager class (lines ~700-1400)
   - AudioStreamer class (lines ~1400-1600)
   - main() function (lines ~1600-1700)

2. **Create Custom System Prompt** (replace retail prompt):
```python
call_center_system_prompt = (
    "You are a helpful phone agent for Denver Warehouse Club call center. "
    "You assist members calling about store hours, product availability, "
    "curbside orders, appointments, and specialty orders like cakes.\n\n"
    "PERSONALITY:\n"
    "- Warm, friendly, professional phone manner\n"
    "- Patient and helpful (members can't see, only hear)\n"
    "- Clear enunciation for phone clarity\n"
    "- Confirm information verbally\n\n"
    "PHONE ETIQUETTE:\n"
    "1. Greet: 'Thank you for calling Denver Warehouse Club, how can I help you?'\n"
    "2. Verify if needed: 'May I have your phone number or member ID?'\n"
    "3. Assist: Use tools to answer questions\n"
    "4. Confirm: Repeat key info (confirmation numbers, dates, times)\n"
    "5. Close: 'Is there anything else?' then 'Thank you for calling!'\n\n"
    "TOOLS USAGE:\n"
    "- verifyMemberTool: For personal account questions\n"
    "- checkStoreHoursTool: Hours queries (today, holidays, departments)\n"
    "- checkInventoryTool: Product availability\n"
    "- checkCurbsideOrderTool: Online order status\n"
    "- scheduleAppointmentTool: Book Tire/Optical/Hearing/Pharmacy\n"
    "- checkSpecialtyOrderTool: Cake order status\n"
    "- createCakeOrderTool: New cake orders (48-hr lead time)\n"
    "- checkAppointmentTool: Verify existing appointments\n\n"
    "IMPORTANT:\n"
    "- Speak clearly and at moderate pace (phone conversation)\n"
    "- Repeat confirmation numbers slowly\n"
    "- Offer to transfer to department if you can't help\n"
    "- Be patient with elderly callers or language barriers"
)
```

3. **Create Streamlit Dashboard** adapted for call center metrics

4. **Test Phone Scenarios** with various member requests

## Support

For questions or issues:
- Check AWS Bedrock quotas
- Verify DynamoDB tables exist
- Review tool execution logs with `--debug`
- Test tools individually before full agent

---

**Status:** Database and tools complete. Streaming infrastructure to be added.
**Template:** Copy from Customer_Service_Agent and customize system prompt.
