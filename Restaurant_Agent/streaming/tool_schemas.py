"""
Tool Schemas
JSON schemas for all restaurant agent tools
"""
import json


def get_tool_schemas():
    """Returns all tool schemas for the restaurant agent"""

    lookup_reservation_schema = {
        "type": "object",
        "properties": {
            "phone": {"type": "string", "description": "Customer phone number (preferred for lookup)"},
            "customerName": {"type": "string", "description": "Customer name (partial match supported)"},
            "reservationId": {"type": "string", "description": "Reservation confirmation number"}
        }
    }

    create_reservation_schema = {
        "type": "object",
        "properties": {
            "customerName": {"type": "string"},
            "phone": {"type": "string"},
            "partySize": {"type": "integer"},
            "reservationDate": {"type": "string", "description": "YYYY-MM-DD format"},
            "reservationTime": {"type": "string", "description": "Time in format like '7:00 PM'"},
            "highChairNeeded": {"type": "boolean", "default": False},
            "accessibilityNeeded": {"type": "boolean", "default": False},
            "seatingPreference": {"type": "string", "description": "Window, Patio, Main Dining, or Private Room"},
            "specialRequests": {"type": "string"}
        },
        "required": ["customerName", "phone", "partySize", "reservationDate", "reservationTime"]
    }

    edit_reservation_schema = {
        "type": "object",
        "properties": {
            "reservationId": {"type": "string"},
            "phone": {"type": "string", "description": "Alternative to reservationId"},
            "newPartySize": {"type": "integer"},
            "newReservationDate": {"type": "string"},
            "newReservationTime": {"type": "string"},
            "newSpecialRequests": {"type": "string"},
            "newSeatingPreference": {"type": "string"}
        }
    }

    cancel_reservation_schema = {
        "type": "object",
        "properties": {
            "reservationId": {"type": "string"},
            "phone": {"type": "string", "description": "Alternative to reservationId"}
        }
    }

    confirm_reservation_schema = {
        "type": "object",
        "properties": {
            "reservationId": {"type": "string"},
            "phone": {"type": "string", "description": "Alternative to reservationId"}
        }
    }

    join_waitlist_schema = {
        "type": "object",
        "properties": {
            "customerName": {"type": "string"},
            "phone": {"type": "string"},
            "partySize": {"type": "integer"},
            "requestedDate": {"type": "string", "description": "Optional: YYYY-MM-DD"},
            "requestedTime": {"type": "string", "description": "Optional: desired time if joining reservation waitlist"},
            "highChairNeeded": {"type": "boolean", "default": False},
            "accessibilityNeeded": {"type": "boolean", "default": False},
            "seatingPreference": {"type": "string"},
            "type": {"type": "string", "enum": ["Walk-in", "Reservation Waitlist"], "default": "Walk-in"}
        },
        "required": ["customerName", "phone", "partySize"]
    }

    check_wait_time_schema = {
        "type": "object",
        "properties": {
            "partySize": {"type": "integer"}
        },
        "required": ["partySize"]
    }

    notify_table_ready_schema = {
        "type": "object",
        "properties": {
            "waitlistId": {"type": "string"}
        },
        "required": ["waitlistId"]
    }

    seat_guest_schema = {
        "type": "object",
        "properties": {
            "reservationId": {"type": "string"},
            "waitlistId": {"type": "string"}
        }
    }

    place_order_schema = {
        "type": "object",
        "properties": {
            "reservationId": {"type": "string"},
            "customerName": {"type": "string"},
            "tableId": {"type": "string"},
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "itemId": {"type": "string"},
                        "quantity": {"type": "integer", "default": 1},
                        "specialInstructions": {"type": "string"}
                    },
                    "required": ["itemId"]
                }
            },
            "specialRequests": {"type": "string"}
        },
        "required": ["items"]
    }

    view_menu_schema = {
        "type": "object",
        "properties": {
            "category": {"type": "string", "description": "Optional: Appetizer, Entree, Dessert, or Beverage"}
        }
    }

    check_order_status_schema = {
        "type": "object",
        "properties": {
            "orderId": {"type": "string"},
            "tableId": {"type": "string"}
        }
    }

    # Return tool specifications
    return [
        {
            "toolSpec": {
                "name": "lookupReservationTool",
                "description": "Look up existing reservation by phone number, name, or reservation ID. Use phone number first if customer doesn't remember name.",
                "inputSchema": {"json": lookup_reservation_schema},
            }
        },
        {
            "toolSpec": {
                "name": "createReservationTool",
                "description": "Create a new reservation with party size, date, time, and preferences (high chair, accessibility, seating).",
                "inputSchema": {"json": create_reservation_schema},
            }
        },
        {
            "toolSpec": {
                "name": "editReservationTool",
                "description": "Modify an existing reservation (party size, date, time, special requests).",
                "inputSchema": {"json": edit_reservation_schema},
            }
        },
        {
            "toolSpec": {
                "name": "cancelReservationTool",
                "description": "Cancel a reservation by ID or phone number.",
                "inputSchema": {"json": cancel_reservation_schema},
            }
        },
        {
            "toolSpec": {
                "name": "confirmReservationTool",
                "description": "Confirm details of an existing reservation.",
                "inputSchema": {"json": confirm_reservation_schema},
            }
        },
        {
            "toolSpec": {
                "name": "joinWaitlistTool",
                "description": "Add customer to waitlist for walk-in or fully booked reservation time.",
                "inputSchema": {"json": join_waitlist_schema},
            }
        },
        {
            "toolSpec": {
                "name": "checkWaitTimeTool",
                "description": "Quote current estimated wait time for walk-in guests.",
                "inputSchema": {"json": check_wait_time_schema},
            }
        },
        {
            "toolSpec": {
                "name": "notifyTableReadyTool",
                "description": "Send notification to customer that their table is ready.",
                "inputSchema": {"json": notify_table_ready_schema},
            }
        },
        {
            "toolSpec": {
                "name": "seatGuestTool",
                "description": "Mark guest as seated (from reservation or waitlist).",
                "inputSchema": {"json": seat_guest_schema},
            }
        },
        {
            "toolSpec": {
                "name": "placeOrderTool",
                "description": "Place food order for seated guest with menu items.",
                "inputSchema": {"json": place_order_schema},
            }
        },
        {
            "toolSpec": {
                "name": "viewMenuTool",
                "description": "View available menu items, optionally filtered by category.",
                "inputSchema": {"json": view_menu_schema},
            }
        },
        {
            "toolSpec": {
                "name": "checkOrderStatusTool",
                "description": "Check status of a food order.",
                "inputSchema": {"json": check_order_status_schema},
            }
        },
    ]
