"""
Tool Schema Definitions for Call Center Agent
Defines all available tools for call center operations
"""
import json


def get_tool_schemas():
    """Returns a list of all tool schema definitions for the call center agent"""

    # Verify member by phone number or member ID
    verify_member_schema = json.dumps({
        "type": "object",
        "properties": {
            "memberId": {"type": "string", "description": "Member ID if known."},
            "phone": {"type": "string", "description": "Phone number for verification."}
        }
    })

    # Check store hours
    check_store_hours_schema = json.dumps({
        "type": "object",
        "properties": {
            "storeId": {"type": "string", "default": "STORE-4523"},
            "queryType": {
                "type": "string",
                "description": "Type of hours query: 'regular', 'holiday', 'department', 'today'",
                "default": "today"
            },
            "department": {"type": "string", "description": "Department name for department-specific hours"}
        }
    })

    # Check inventory
    check_inventory_schema = json.dumps({
        "type": "object",
        "properties": {
            "sku": {"type": "string"},
            "productName": {"type": "string"}
        }
    })

    # Check curbside order
    check_curbside_schema = json.dumps({
        "type": "object",
        "properties": {
            "orderId": {"type": "string"},
            "memberId": {"type": "string"}
        }
    })

    # Schedule appointment
    schedule_appointment_schema = json.dumps({
        "type": "object",
        "properties": {
            "memberId": {"type": "string"},
            "memberName": {"type": "string"},
            "department": {"type": "string", "description": "TireCenter, OpticalCenter, HearingAidCenter, or Pharmacy"},
            "serviceType": {"type": "string"},
            "appointmentDate": {"type": "string", "description": "YYYY-MM-DD format"},
            "appointmentTime": {"type": "string"},
            "notes": {"type": "string"}
        },
        "required": ["memberId", "department", "serviceType", "appointmentDate", "appointmentTime"]
    })

    # Check specialty order
    check_specialty_order_schema = json.dumps({
        "type": "object",
        "properties": {
            "orderId": {"type": "string"},
            "memberId": {"type": "string"},
            "orderType": {"type": "string", "default": "Cake"}
        }
    })

    # Create cake order
    create_cake_order_schema = json.dumps({
        "type": "object",
        "properties": {
            "memberId": {"type": "string"},
            "memberName": {"type": "string"},
            "size": {"type": "string", "description": "Quarter Sheet, Half Sheet, or Full Sheet"},
            "flavor": {"type": "string"},
            "inscription": {"type": "string"},
            "decorations": {"type": "string"},
            "pickupDate": {"type": "string", "description": "YYYY-MM-DD format"},
            "pickupTime": {"type": "string"}
        },
        "required": ["memberId", "size", "flavor", "pickupDate"]
    })

    # Check appointment
    check_appointment_schema = json.dumps({
        "type": "object",
        "properties": {
            "confirmationNumber": {"type": "string"},
            "memberId": {"type": "string"},
            "department": {"type": "string"}
        }
    })

    # Return the list of tool specifications
    return [
        {
            "toolSpec": {
                "name": "verifyMemberTool",
                "description": "Verify member by phone number or member ID. Use for personal account questions.",
                "inputSchema": {"json": verify_member_schema}
            }
        },
        {
            "toolSpec": {
                "name": "checkStoreHoursTool",
                "description": "Check store hours (regular, holiday, department-specific, or today's hours).",
                "inputSchema": {"json": check_store_hours_schema}
            }
        },
        {
            "toolSpec": {
                "name": "checkInventoryTool",
                "description": "Check if a product is in stock, get aisle location and price.",
                "inputSchema": {"json": check_inventory_schema}
            }
        },
        {
            "toolSpec": {
                "name": "checkCurbsideOrderTool",
                "description": "Check curbside order status by order ID or member ID.",
                "inputSchema": {"json": check_curbside_schema}
            }
        },
        {
            "toolSpec": {
                "name": "scheduleAppointmentTool",
                "description": "Schedule an appointment at Tire Center, Optical, Hearing Aid, or Pharmacy.",
                "inputSchema": {"json": schedule_appointment_schema}
            }
        },
        {
            "toolSpec": {
                "name": "checkSpecialtyOrderTool",
                "description": "Check status of cake or custom orders.",
                "inputSchema": {"json": check_specialty_order_schema}
            }
        },
        {
            "toolSpec": {
                "name": "createCakeOrderTool",
                "description": "Create a new cake order (requires 48-hour lead time).",
                "inputSchema": {"json": create_cake_order_schema}
            }
        },
        {
            "toolSpec": {
                "name": "checkAppointmentTool",
                "description": "Check existing appointment by confirmation number or member ID.",
                "inputSchema": {"json": check_appointment_schema}
            }
        }
    ]
