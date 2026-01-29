"""
Tool Schemas for AWS Bedrock
Contains all 21 banking tool definitions with input schemas
"""
import json
from config.constants import *


def get_tool_schemas():
    """Returns all 21 banking tool schemas for AWS Bedrock"""

    # Authentication Tools (3)
    authenticate_schema = {
        "type": "object",
        "properties": {
            "phone": {"type": "string", "description": "Customer phone number for authentication"}
        },
        "required": ["phone"]
    }

    verify_otp_schema = {
        "type": "object",
        "properties": {
            "otp": {"type": "string", "description": "6-digit one-time password received via SMS"}
        },
        "required": ["otp"]
    }

    step_up_authentication_schema = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["get_question", "verify_answer"], "description": "Get security question or verify answer"},
            "answer": {"type": "string", "description": "Answer to security question (required if action is verify_answer)"}
        },
        "required": ["action"]
    }

    # Account Information Tools (4)
    check_balance_schema = {
        "type": "object",
        "properties": {
            "accountId": {"type": "string", "description": "Optional: specific account ID to check"}
        }
    }

    view_recent_transactions_schema = {
        "type": "object",
        "properties": {
            "accountId": {"type": "string", "description": "Account ID to view transactions"}
        },
        "required": ["accountId"]
    }

    search_transactions_schema = {
        "type": "object",
        "properties": {
            "accountId": {"type": "string"},
            "merchant": {"type": "string", "description": "Filter by merchant name"},
            "minAmount": {"type": "number", "description": "Minimum transaction amount"},
            "maxAmount": {"type": "number", "description": "Maximum transaction amount"},
            "startDate": {"type": "string", "description": "YYYY-MM-DD format"},
            "endDate": {"type": "string", "description": "YYYY-MM-DD format"},
            "category": {"type": "string", "description": "Category like Dining, Gas, etc."}
        },
        "required": ["accountId"]
    }

    request_statement_schema = {
        "type": "object",
        "properties": {
            "accountId": {"type": "string"},
            "statementMonth": {"type": "string", "description": "YYYY-MM format"},
            "deliveryMethod": {"type": "string", "enum": ["email", "mail", "download"], "default": "email"}
        },
        "required": ["accountId", "statementMonth"]
    }

    # Card Services Tools (6)
    report_lost_card_schema = {
        "type": "object",
        "properties": {
            "cardId": {"type": "string"},
            "reason": {"type": "string", "enum": ["lost", "stolen"], "description": "Whether card is lost or stolen"}
        },
        "required": ["cardId", "reason"]
    }

    freeze_card_schema = {
        "type": "object",
        "properties": {
            "cardId": {"type": "string"}
        },
        "required": ["cardId"]
    }

    unfreeze_card_schema = {
        "type": "object",
        "properties": {
            "cardId": {"type": "string"}
        },
        "required": ["cardId"]
    }

    check_replacement_status_schema = {
        "type": "object",
        "properties": {
            "cardId": {"type": "string", "description": "Original card ID"}
        },
        "required": ["cardId"]
    }

    dispute_charge_schema = {
        "type": "object",
        "properties": {
            "transactionId": {"type": "string"},
            "reason": {"type": "string", "description": "Reason for dispute"},
            "description": {"type": "string", "description": "Detailed description of the dispute"}
        },
        "required": ["transactionId", "reason"]
    }

    clarify_merchant_schema = {
        "type": "object",
        "properties": {
            "transactionId": {"type": "string"},
            "merchantCode": {"type": "string", "description": "Merchant code like SQ*ABC123"}
        },
        "required": ["transactionId"]
    }

    # Payment & Transfer Tools (5)
    internal_transfer_schema = {
        "type": "object",
        "properties": {
            "fromAccountId": {"type": "string"},
            "toAccountId": {"type": "string"},
            "amount": {"type": "number"},
            "memo": {"type": "string"}
        },
        "required": ["fromAccountId", "toAccountId", "amount"]
    }

    check_zelle_status_schema = {
        "type": "object",
        "properties": {
            "transferId": {"type": "string", "description": "Zelle transfer ID"}
        },
        "required": ["transferId"]
    }

    setup_billpay_schema = {
        "type": "object",
        "properties": {
            "payeeName": {"type": "string"},
            "accountNumber": {"type": "string"},
            "payeeAddress": {"type": "string"},
            "amount": {"type": "number"},
            "paymentDate": {"type": "string", "description": "YYYY-MM-DD format"},
            "recurring": {"type": "boolean", "default": False},
            "frequency": {"type": "string", "description": "monthly, weekly, etc. if recurring"}
        },
        "required": ["payeeName", "accountNumber", "amount", "paymentDate"]
    }

    stop_payment_schema = {
        "type": "object",
        "properties": {
            "checkNumber": {"type": "string"},
            "accountId": {"type": "string"},
            "amount": {"type": "number"},
            "payee": {"type": "string"}
        },
        "required": ["checkNumber", "accountId"]
    }

    explain_pending_schema = {
        "type": "object",
        "properties": {
            "transactionId": {"type": "string", "description": "Optional: specific transaction to explain"}
        }
    }

    # Fraud & Dispute Tools (3)
    report_fraud_schema = {
        "type": "object",
        "properties": {
            "fraudType": {"type": "string", "enum": ["card", "account", "identity"], "description": "Type of fraud"},
            "description": {"type": "string", "description": "Description of fraudulent activity"},
            "affectedCardId": {"type": "string", "description": "If card fraud, the card ID"},
            "affectedAccountId": {"type": "string", "description": "If account fraud, the account ID"},
            "suspiciousTransactionIds": {"type": "array", "items": {"type": "string"}, "description": "List of suspicious transaction IDs"}
        },
        "required": ["fraudType", "description"]
    }

    check_dispute_status_schema = {
        "type": "object",
        "properties": {
            "disputeId": {"type": "string"}
        },
        "required": ["disputeId"]
    }

    explain_provisional_credit_schema = {
        "type": "object",
        "properties": {
            "disputeId": {"type": "string", "description": "Optional: specific dispute to explain"}
        }
    }

    # Return all 21 tools with schemas
    return [
        # Authentication Tools (3)
        {
            "toolSpec": {
                "name": "authenticateTool",
                "description": "Authenticate customer by phone number. This creates a Level 1 session for basic banking operations. Call disclosure is recorded.",
                "inputSchema": {"json": authenticate_schema},
            }
        },
        {
            "toolSpec": {
                "name": "verifyOtpTool",
                "description": "Verify one-time password (OTP) sent via SMS. Upgrades authentication to Level 2 for medium-risk operations.",
                "inputSchema": {"json": verify_otp_schema},
            }
        },
        {
            "toolSpec": {
                "name": "stepUpAuthenticationTool",
                "description": "Step-up authentication for high-risk operations. Get security question or verify answer to reach Level 3.",
                "inputSchema": {"json": step_up_authentication_schema},
            }
        },

        # Account Information Tools (4 - Level 1)
        {
            "toolSpec": {
                "name": "checkBalanceTool",
                "description": "Check account balance showing available vs pending amounts. Requires Level 1 authentication.",
                "inputSchema": {"json": check_balance_schema},
            }
        },
        {
            "toolSpec": {
                "name": "viewRecentTransactionsTool",
                "description": "View last 10 transactions for an account. Requires Level 1 authentication.",
                "inputSchema": {"json": view_recent_transactions_schema},
            }
        },
        {
            "toolSpec": {
                "name": "searchTransactionsTool",
                "description": "Search transactions by merchant, amount range, date range, or category. Requires Level 1 authentication.",
                "inputSchema": {"json": search_transactions_schema},
            }
        },
        {
            "toolSpec": {
                "name": "requestStatementTool",
                "description": "Request monthly account statement via email, mail, or download. Requires Level 1 authentication.",
                "inputSchema": {"json": request_statement_schema},
            }
        },

        # Card Services Tools (6)
        {
            "toolSpec": {
                "name": "reportLostCardTool",
                "description": "Report card as lost or stolen. Immediately deactivates card. Requires Level 1 authentication.",
                "inputSchema": {"json": report_lost_card_schema},
            }
        },
        {
            "toolSpec": {
                "name": "freezeCardTool",
                "description": "Temporarily freeze card (can be unfrozen later). Requires Level 1 authentication.",
                "inputSchema": {"json": freeze_card_schema},
            }
        },
        {
            "toolSpec": {
                "name": "unfreezeCardTool",
                "description": "Unfreeze a previously frozen card. Requires Level 2 authentication (OTP).",
                "inputSchema": {"json": unfreeze_card_schema},
            }
        },
        {
            "toolSpec": {
                "name": "checkReplacementStatusTool",
                "description": "Check status of card replacement. Requires Level 1 authentication.",
                "inputSchema": {"json": check_replacement_status_schema},
            }
        },
        {
            "toolSpec": {
                "name": "disputeChargeTool",
                "description": "Dispute a charge on account. Creates dispute case with 30-day resolution timeline. Requires Level 2 authentication (OTP).",
                "inputSchema": {"json": dispute_charge_schema},
            }
        },
        {
            "toolSpec": {
                "name": "clarifyMerchantTool",
                "description": "Clarify merchant name/code (like SQ*, TST*) for a transaction. Requires Level 1 authentication.",
                "inputSchema": {"json": clarify_merchant_schema},
            }
        },

        # Payment & Transfer Tools (5)
        {
            "toolSpec": {
                "name": "internalTransferTool",
                "description": "Transfer money between customer's own accounts. Instant transfer. Requires Level 2 authentication (OTP).",
                "inputSchema": {"json": internal_transfer_schema},
            }
        },
        {
            "toolSpec": {
                "name": "checkZelleStatusTool",
                "description": "Check status of Zelle, ACH, or wire transfer. Requires Level 1 authentication.",
                "inputSchema": {"json": check_zelle_status_schema},
            }
        },
        {
            "toolSpec": {
                "name": "setupBillpayTool",
                "description": "Set up bill payment (one-time or recurring). Requires Level 2 authentication (OTP).",
                "inputSchema": {"json": setup_billpay_schema},
            }
        },
        {
            "toolSpec": {
                "name": "stopPaymentTool",
                "description": "Stop payment on check ($35 fee). HIGH-RISK: Requires Level 3 authentication (OTP + security question).",
                "inputSchema": {"json": stop_payment_schema},
            }
        },
        {
            "toolSpec": {
                "name": "explainPendingTool",
                "description": "Explain difference between pending and posted transactions. Educational tool, requires Level 1 authentication.",
                "inputSchema": {"json": explain_pending_schema},
            }
        },

        # Fraud & Dispute Tools (3)
        {
            "toolSpec": {
                "name": "reportFraudTool",
                "description": "Report fraudulent activity on card or account. Deactivates affected card immediately. Requires Level 2 authentication (OTP).",
                "inputSchema": {"json": report_fraud_schema},
            }
        },
        {
            "toolSpec": {
                "name": "checkDisputeStatusTool",
                "description": "Check status of fraud/dispute case. Requires Level 1 authentication.",
                "inputSchema": {"json": check_dispute_status_schema},
            }
        },
        {
            "toolSpec": {
                "name": "explainProvisionalCreditTool",
                "description": "Explain provisional credit process under Regulation E. Educational tool, requires Level 1 authentication.",
                "inputSchema": {"json": explain_provisional_credit_schema},
            }
        },
    ]
