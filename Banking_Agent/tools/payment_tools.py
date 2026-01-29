"""
Payment & Transfer Tools
Handles internal transfers, Zelle status, bill pay, stop payments, and transaction education
"""
import datetime
import random
from decimal import Decimal
from typing import Dict, Any
from tools.base_tool import BaseTool
from config.constants import *


class InternalTransferTool(BaseTool):
    """Transfer money between customer's own accounts"""

    def __init__(self, dynamodb, auth_manager, accounts_table, transfers_table):
        super().__init__(dynamodb, auth_manager)
        self.accounts_table = accounts_table
        self.transfers_table = transfers_table

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        LEVEL: Level 2 (OTP required)
        Transfer money between customer's own accounts
        """
        try:
            authorized, error, _ = self.check_auth_level(AUTH_LEVEL_2)
            if not authorized:
                return error

            customer_id, error = self.get_customer_id()
            if error:
                return error

            from_account_id = content_data.get("fromAccountId")
            to_account_id = content_data.get("toAccountId")
            amount = content_data.get("amount")

            if not all([from_account_id, to_account_id, amount]):
                return {"error": "fromAccountId, toAccountId, and amount are required"}

            # Verify both accounts belong to customer
            from_account = self.accounts_table.get_item(Key={'accountId': from_account_id})
            to_account = self.accounts_table.get_item(Key={'accountId': to_account_id})

            if 'Item' not in from_account or 'Item' not in to_account:
                return {"error": "One or both accounts not found"}

            if from_account['Item']['customerId'] != customer_id or to_account['Item']['customerId'] != customer_id:
                return {"error": "Unauthorized - accounts must belong to you"}

            from_acc = from_account['Item']
            to_acc = to_account['Item']

            # Check sufficient funds
            if float(from_acc['availableBalance']) < float(amount):
                return {
                    "success": False,
                    "message": f"Insufficient funds. Available balance: ${from_acc['availableBalance']}, Transfer amount: ${amount}"
                }

            # Create transfer record
            transfer_id = f"XFER-{datetime.datetime.now().strftime('%Y%m%d')}-{random.randint(100, 999)}"

            transfer = {
                'transferId': transfer_id,
                'customerId': customer_id,
                'fromAccountId': from_account_id,
                'toAccountId': to_account_id,
                'amount': Decimal(str(amount)),
                'transferType': 'Internal',
                'status': 'Completed',  # Internal transfers are instant
                'scheduledDate': datetime.date.today().strftime('%Y-%m-%d'),
                'completedDate': datetime.date.today().strftime('%Y-%m-%d'),
                'description': f'Transfer from {from_acc["accountNumber"]} to {to_acc["accountNumber"]}',
                'initiatedAt': datetime.datetime.now().isoformat()
            }

            self.transfers_table.put_item(Item=transfer)

            # Update account balances
            new_from_balance = Decimal(str(from_acc['balance'])) - Decimal(str(amount))
            new_to_balance = Decimal(str(to_acc['balance'])) + Decimal(str(amount))

            self.accounts_table.update_item(
                Key={'accountId': from_account_id},
                UpdateExpression="SET balance = :bal, availableBalance = :bal",
                ExpressionAttributeValues={':bal': new_from_balance}
            )

            self.accounts_table.update_item(
                Key={'accountId': to_account_id},
                UpdateExpression="SET balance = :bal, availableBalance = :bal",
                ExpressionAttributeValues={':bal': new_to_balance}
            )

            self.audit_action('INTERNAL_TRANSFER', transfer_id, AUDIT_RESULT_SUCCESS)

            return {
                "success": True,
                "transferId": transfer_id,
                "fromAccount": from_acc['accountNumber'],
                "toAccount": to_acc['accountNumber'],
                "amount": str(amount),
                "status": "Completed",
                "newFromBalance": str(new_from_balance),
                "newToBalance": str(new_to_balance),
                "message": f"Transfer complete! ${amount} has been moved from your {from_acc['accountType']} account to your {to_acc['accountType']} account. The funds are available immediately."
            }

        except Exception as e:
            self.audit_action('INTERNAL_TRANSFER', None, AUDIT_RESULT_FAILURE)
            return {"error": str(e)}


class CheckZelleStatusTool(BaseTool):
    """Check status of Zelle/ACH/wire transfer"""

    def __init__(self, dynamodb, auth_manager, transfers_table):
        super().__init__(dynamodb, auth_manager)
        self.transfers_table = transfers_table

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        LEVEL: Level 1 (phone verified)
        Check status of Zelle/ACH/wire transfer
        """
        try:
            authorized, error, _ = self.check_auth_level(AUTH_LEVEL_1)
            if not authorized:
                return error

            customer_id, error = self.get_customer_id()
            if error:
                return error

            transfer_id = content_data.get("transferId")

            if not transfer_id:
                return {"error": "transferId is required"}

            # Get transfer
            response = self.transfers_table.get_item(Key={'transferId': transfer_id})
            if 'Item' not in response:
                return {"found": False, "message": "Transfer not found"}

            transfer = response['Item']

            # Verify ownership
            if transfer['customerId'] != customer_id:
                return {"error": "Unauthorized"}

            transfer = self.convert_decimals(transfer)

            self.audit_action('CHECK_ZELLE_STATUS', transfer_id, AUDIT_RESULT_SUCCESS)

            # Status explanations
            status_messages = {
                'Pending': 'Your transfer is being processed. Zelle transfers typically complete within minutes, ACH within 1-3 business days, and wires same day.',
                'Completed': 'Your transfer has been completed successfully.',
                'Failed': 'Your transfer failed. Please contact us for details.',
                'Cancelled': 'This transfer was cancelled.'
            }

            return {
                "found": True,
                "transfer": transfer,
                "status": transfer['status'],
                "message": status_messages.get(transfer['status'], 'Transfer status unknown')
            }

        except Exception as e:
            self.audit_action('CHECK_ZELLE_STATUS', None, AUDIT_RESULT_FAILURE)
            return {"error": str(e)}


class SetupBillpayTool(BaseTool):
    """Setup or modify bill pay for a payee"""

    def __init__(self, dynamodb, auth_manager, accounts_table, billpay_table):
        super().__init__(dynamodb, auth_manager)
        self.accounts_table = accounts_table
        self.billpay_table = billpay_table

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        LEVEL: Level 2 (OTP required)
        Setup or modify bill pay for a payee
        """
        try:
            authorized, error, _ = self.check_auth_level(AUTH_LEVEL_2)
            if not authorized:
                return error

            customer_id, error = self.get_customer_id()
            if error:
                return error

            payee_name = content_data.get("payeeName")
            account_number = content_data.get("accountNumber")  # Masked
            payee_address = content_data.get("payeeAddress")
            from_account_id = content_data.get("fromAccountId")
            recurring = content_data.get("recurringPayment", False)
            amount = content_data.get("amount")
            frequency = content_data.get("frequency")  # "Monthly", "Weekly", etc.
            next_payment_date = content_data.get("nextPaymentDate")

            if not all([payee_name, from_account_id]):
                return {"error": "payeeName and fromAccountId are required"}

            # Verify account ownership
            account = self.accounts_table.get_item(Key={'accountId': from_account_id})
            if 'Item' not in account or account['Item']['customerId'] != customer_id:
                return {"error": "Unauthorized account"}

            # Create payee
            payee_id = f"PAYEE-{random.randint(100, 999)}"

            payee = {
                'payeeId': payee_id,
                'customerId': customer_id,
                'payeeName': payee_name,
                'accountNumber': account_number,
                'payeeAddress': payee_address,
                'paymentMethod': 'Electronic',
                'recurringPayment': recurring,
                'amount': Decimal(str(amount)) if amount else None,
                'frequency': frequency,
                'nextPaymentDate': next_payment_date,
                'fromAccountId': from_account_id,
                'status': 'Active'
            }

            self.billpay_table.put_item(Item=payee)

            self.audit_action('SETUP_BILLPAY', payee_id, AUDIT_RESULT_SUCCESS)

            return {
                "success": True,
                "payeeId": payee_id,
                "payeeName": payee_name,
                "recurring": recurring,
                "message": f"Bill pay setup complete for {payee_name}. " +
                          (f"Recurring payments of ${amount} will be sent {frequency}. Next payment: {next_payment_date}" if recurring else "You can now make one-time payments to this payee.")
            }

        except Exception as e:
            self.audit_action('SETUP_BILLPAY', None, AUDIT_RESULT_FAILURE)
            return {"error": str(e)}


class StopPaymentTool(BaseTool):
    """Place stop payment on a check or ACH - requires highest authentication"""

    def __init__(self, dynamodb, auth_manager, accounts_table):
        super().__init__(dynamodb, auth_manager)
        self.accounts_table = accounts_table

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        LEVEL: Level 3 (highest security - requires knowledge question)
        Place stop payment on a check or ACH
        """
        try:
            # Check authorization - Level 3 required
            authorized, error, _ = self.check_auth_level(AUTH_LEVEL_3)
            if not authorized:
                return error

            customer_id, error = self.get_customer_id()
            if error:
                return error

            account_id = content_data.get("accountId")
            check_number = content_data.get("checkNumber")
            amount = content_data.get("amount")
            payee = content_data.get("payee")

            if not all([account_id, check_number]):
                return {"error": "accountId and checkNumber are required"}

            # Verify account
            account = self.accounts_table.get_item(Key={'accountId': account_id})
            if 'Item' not in account or account['Item']['customerId'] != customer_id:
                return {"error": "Unauthorized"}

            # Create stop payment record (would be in separate table in production)
            stop_id = f"STOP-{datetime.datetime.now().strftime('%Y%m%d')}-{random.randint(100, 999)}"

            self.audit_action('STOP_PAYMENT', stop_id, AUDIT_RESULT_SUCCESS)

            return {
                "success": True,
                "stopPaymentId": stop_id,
                "checkNumber": check_number,
                "account": account['Item']['accountNumber'],
                "fee": "35.00",
                "message": f"Stop payment placed on check #{check_number}. A $35 fee will be charged to your account. The stop payment is effective immediately and valid for 6 months. If the check is presented, it will be returned unpaid."
            }

        except Exception as e:
            self.audit_action('STOP_PAYMENT', None, AUDIT_RESULT_FAILURE)
            return {"error": str(e)}


class ExplainPendingTool(BaseTool):
    """Educational tool: Explain difference between pending vs posted transactions"""

    def __init__(self, dynamodb, auth_manager):
        super().__init__(dynamodb, auth_manager)

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        LEVEL: Level 1 (phone verified)
        Explain difference between pending vs posted transactions
        """
        try:
            authorized, error, _ = self.check_auth_level(AUTH_LEVEL_1)
            if not authorized:
                return error

            # Educational response
            explanation = {
                "pending": "Pending transactions are charges that have been authorized but not yet fully processed by the merchant. They reduce your available balance but haven't been deducted from your actual balance yet.",
                "posted": "Posted transactions have been fully processed and settled. They've been deducted from both your available balance and actual balance.",
                "timeline": "Most pending transactions post within 1-3 business days. Gas stations and hotels may hold funds longer (up to 7 days).",
                "availableBalance": "Your available balance = actual balance minus pending transactions. This is what you can actually spend.",
                "actualBalance": "Your actual balance is the total in your account, not accounting for pending holds."
            }

            self.audit_action('EXPLAIN_PENDING', None, AUDIT_RESULT_SUCCESS)

            return {
                "success": True,
                "explanation": explanation,
                "message": "Pending transactions have been authorized but not yet fully processed. They reduce your available balance immediately. Posted transactions have been settled and deducted from your actual balance. Most pending transactions post within 1-3 business days."
            }

        except Exception as e:
            return {"error": str(e)}
