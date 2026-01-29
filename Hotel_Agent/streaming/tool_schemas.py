"""
Tool Schemas for Hotel Agent
Contains the 3 hotel tool definitions with input schemas
"""
import json


def get_tool_schemas():
    """Returns all 3 hotel tool schemas for AWS Bedrock"""

    # Guest Profile Tool
    guest_tool_schema = {
        "type": "object",
        "properties": {
            "guestName": {
                "type": "string",
                "description": "The full name of the hotel guest.",
            }
        },
        "required": ["guestName"],
    }

    # Reservation Status Tool
    reservation_tool_schema = {
        "type": "object",
        "properties": {
            "guestName": {
                "type": "string",
                "description": "The full name of the hotel guest.",
            },
            "includePastStays": {
                "type": "boolean",
                "description": "If true, also return past stays.",
                "default": False,
            },
        },
        "required": ["guestName"],
    }

    # Update Reservation Tool
    update_reservation_tool_schema = {
        "type": "object",
        "properties": {
            "reservationId": {
                "type": "string",
                "description": "The reservation ID to update (e.g., 'RES-1001').",
            },
            "newRoomType": {
                "type": "string",
                "description": "New room type to set (e.g., 'King Deluxe'). Optional.",
            },
            "newSpecialRequest": {
                "type": "string",
                "description": "A short note to append to specialRequests, e.g. 'Feather-free pillows'. Optional.",
            },
        },
        "required": ["reservationId"],
    }

    # Return all 3 tools with schemas
    return [
        {
            "toolSpec": {
                "name": "checkGuestProfileTool",
                "description": (
                    "Use this tool to look up a hotel guest's profile in the hotel system. "
                    "It returns DOB for identity verification, loyalty tier, and preferences."
                ),
                "inputSchema": {"json": json.dumps(guest_tool_schema)},
            }
        },
        {
            "toolSpec": {
                "name": "checkReservationStatusTool",
                "description": (
                    "Use this tool to check the guest's upcoming reservation and, optionally, past stays. "
                    "Call this after verifying identity to answer questions about bookings or balances."
                ),
                "inputSchema": {"json": json.dumps(reservation_tool_schema)},
            }
        },
        {
            "toolSpec": {
                "name": "updateReservationTool",
                "description": (
                    "Use this tool to update an existing reservation's room type and/or add a special request. "
                    "Only use it after the guest clearly confirms what they want to change."
                ),
                "inputSchema": {"json": json.dumps(update_reservation_tool_schema)},
            }
        },
    ]
