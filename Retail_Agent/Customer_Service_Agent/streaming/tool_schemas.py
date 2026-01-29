"""
Tool Schema Definitions for Retail Customer Service Agent
Defines all available tools for member service operations
"""
import json


def get_tool_schemas():
    """Returns a list of all tool schema definitions for the retail agent"""

    # Verify member identity via scanned barcode
    verify_member_schema = json.dumps({
        "type": "object",
        "properties": {
            "memberId": {
                "type": "string",
                "description": "The member ID from the scanned barcode (e.g., 'MEM-100001')."
            }
        },
        "required": ["memberId"]
    })

    # Look up recent transactions or a specific transaction by ID
    lookup_transaction_schema = json.dumps({
        "type": "object",
        "properties": {
            "memberId": {
                "type": "string",
                "description": "The member ID to look up transactions for."
            },
            "transactionId": {
                "type": "string",
                "description": "Optional specific transaction ID to look up."
            },
            "daysBack": {
                "type": "integer",
                "description": "Number of days back to search. Default 30.",
                "default": 30
            }
        },
        "required": ["memberId"]
    })

    # Modify member contact information or payment method
    modify_membership_schema = json.dumps({
        "type": "object",
        "properties": {
            "memberId": {"type": "string", "description": "The member ID."},
            "newPhone": {"type": "string", "description": "New phone number (optional)."},
            "newEmail": {"type": "string", "description": "New email address (optional)."},
            "newAddress": {"type": "string", "description": "New mailing address (optional)."},
            "newPaymentMethod": {
                "type": "object",
                "description": "New payment method with type, last4, expiryDate (optional)."
            }
        },
        "required": ["memberId"]
    })

    # Add a household member to the membership
    add_household_schema = json.dumps({
        "type": "object",
        "properties": {
            "memberId": {"type": "string"},
            "householdMember": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "dob": {"type": "string"},
                    "relationship": {"type": "string"}
                },
                "required": ["name", "dob", "relationship"]
            }
        },
        "required": ["memberId", "householdMember"]
    })

    # Remove a household member from the membership
    remove_household_schema = json.dumps({
        "type": "object",
        "properties": {
            "memberId": {"type": "string"},
            "householdMemberName": {"type": "string"}
        },
        "required": ["memberId", "householdMemberName"]
    })

    # Verify an item using computer vision before return
    verify_return_item_schema = json.dumps({
        "type": "object",
        "properties": {
            "transactionId": {"type": "string"},
            "expectedSku": {"type": "string", "description": "Optional: expected SKU if member told us what they're returning."}
        },
        "required": ["transactionId"]
    })

    # Process a return after CV verification
    initiate_return_schema = json.dumps({
        "type": "object",
        "properties": {
            "memberId": {"type": "string"},
            "transactionId": {"type": "string"},
            "sku": {"type": "string"},
            "quantity": {"type": "integer", "default": 1},
            "reason": {"type": "string", "description": "Reason for return."}
        },
        "required": ["memberId", "transactionId", "sku"]
    })

    # Handle checkout errors like double-scans, missed items, price adjustments
    process_transaction_issue_schema = json.dumps({
        "type": "object",
        "properties": {
            "memberId": {"type": "string"},
            "transactionId": {"type": "string"},
            "issueType": {"type": "string", "description": "Type: 'double_scan', 'missed_item', 'wrong_price'"},
            "itemSku": {"type": "string", "description": "Optional: SKU of the item in question."},
            "adjustmentAmount": {"type": "number", "description": "Refund amount to issue."},
            "description": {"type": "string"}
        },
        "required": ["memberId", "transactionId", "issueType", "adjustmentAmount"]
    })

    # File a customer complaint for tracking and follow-up
    file_complaint_schema = json.dumps({
        "type": "object",
        "properties": {
            "memberId": {"type": "string"},
            "description": {"type": "string", "description": "Description of the complaint."}
        },
        "required": ["memberId", "description"]
    })

    # Return the list of tool specifications
    return [
        {
            "toolSpec": {
                "name": "verifyMemberTool",
                "description": "Verify member identity by scanning their membership barcode. Use this FIRST before any other operations.",
                "inputSchema": {"json": verify_member_schema}
            }
        },
        {
            "toolSpec": {
                "name": "lookupTransactionTool",
                "description": "Look up recent transactions or a specific transaction by ID. Use after member verification.",
                "inputSchema": {"json": lookup_transaction_schema}
            }
        },
        {
            "toolSpec": {
                "name": "modifyMembershipTool",
                "description": "Update member contact info (phone, email, address) or payment method.",
                "inputSchema": {"json": modify_membership_schema}
            }
        },
        {
            "toolSpec": {
                "name": "addHouseholdMemberTool",
                "description": "Add an additional household member to the membership.",
                "inputSchema": {"json": add_household_schema}
            }
        },
        {
            "toolSpec": {
                "name": "removeHouseholdMemberTool",
                "description": "Remove a household member from the membership.",
                "inputSchema": {"json": remove_household_schema}
            }
        },
        {
            "toolSpec": {
                "name": "verifyReturnItemTool",
                "description": "Use computer vision to verify the item placed on the return shelf matches the transaction. Call this BEFORE initiateReturnTool.",
                "inputSchema": {"json": verify_return_item_schema}
            }
        },
        {
            "toolSpec": {
                "name": "initiateReturnTool",
                "description": "Process a return after CV verification. Creates return record and issues refund.",
                "inputSchema": {"json": initiate_return_schema}
            }
        },
        {
            "toolSpec": {
                "name": "processTransactionIssueTool",
                "description": "Handle checkout errors like double-scans, missed items, or price mistakes. Issues adjustment/refund.",
                "inputSchema": {"json": process_transaction_issue_schema}
            }
        },
        {
            "toolSpec": {
                "name": "fileComplaintTool",
                "description": "Log a member complaint for manager review and follow-up.",
                "inputSchema": {"json": file_complaint_schema}
            }
        }
    ]
