"""
Account Information Tools
Handles balance inquiries, transaction viewing, and statement requests
"""
from typing import Dict, Any
from boto3.dynamodb.conditions import Attr
from tools.base_tool import BaseTool
from config.constants import *


class CheckBalanceTool(BaseTool):
    """Check account balance (available vs pending)"""

    def __init__(self, dynamodb, auth_manager, accounts_table):
        super().__init__(dynamodb, auth_manager)
        self.accounts_table = accounts_table

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        LEVEL: Level 1 (phone verified)
        Check account balance (available vs pending)
        """
        try:
            # Check authorization
            authorized, error, current_level = self.check_auth_level(AUTH_LEVEL_1)
            if not authorized:
                return error

            customer_id, error = self.get_customer_id()
            if error:
                return error

            account_type = content_data.get("accountType")

            # Get customer's accounts
            response = self.accounts_table.scan(FilterExpression=Attr('customerId').eq(customer_id))
            accounts = response.get('Items', [])

            if not accounts:
                return {"found": False, "message": "No accounts found"}

            # Filter by type if specified
            if account_type:
                if account_type in ["Checking", "Savings"]:
                    accounts = [a for a in accounts if a['accountType'] == account_type]
                else:
                    # Specific account ID
                    accounts = [a for a in accounts if a['accountId'] == account_type]

            if not accounts:
                return {"found": False, "message": f"No {account_type} account found"}

            # Convert decimals
            accounts = self.convert_decimals(accounts)

            # Audit log
            self.audit_action('CHECK_BALANCE', accounts[0]['accountId'], AUDIT_RESULT_SUCCESS)

            return {
                "found": True,
                "accounts": accounts,
                "count": len(accounts),
                "message": "Here are your account balances. Available balance is what you can spend right now, which accounts for pending transactions."
            }

        except Exception as e:
            self.audit_action('CHECK_BALANCE', None, AUDIT_RESULT_FAILURE)
            return {"error": str(e)}


class ViewRecentTransactionsTool(BaseTool):
    """View recent transactions (last 10 by default)"""

    def __init__(self, dynamodb, auth_manager, transactions_table):
        super().__init__(dynamodb, auth_manager)
        self.transactions_table = transactions_table

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        LEVEL: Level 1 (phone verified)
        View recent transactions (last 10 by default)
        """
        try:
            # Check authorization
            authorized, error, current_level = self.check_auth_level(AUTH_LEVEL_1)
            if not authorized:
                return error

            customer_id, error = self.get_customer_id()
            if error:
                return error

            account_id = content_data.get("accountId")
            limit = content_data.get("limit", 10)

            # Get transactions for this customer
            response = self.transactions_table.scan(FilterExpression=Attr('customerId').eq(customer_id))
            transactions = response.get('Items', [])

            # Filter by account if specified
            if account_id:
                transactions = [t for t in transactions if t['accountId'] == account_id]

            # Sort by date (newest first)
            transactions.sort(key=lambda x: x.get('date', ''), reverse=True)

            # Limit results
            transactions = transactions[:limit]

            # Convert decimals
            transactions = self.convert_decimals(transactions)

            # Audit log
            self.audit_action('VIEW_TRANSACTIONS', account_id, AUDIT_RESULT_SUCCESS)

            return {
                "found": True,
                "transactions": transactions,
                "count": len(transactions),
                "message": f"Here are your {len(transactions)} most recent transactions."
            }

        except Exception as e:
            self.audit_action('VIEW_TRANSACTIONS', None, AUDIT_RESULT_FAILURE)
            return {"error": str(e)}


class SearchTransactionsTool(BaseTool):
    """Search transactions by merchant, amount, date range, or category"""

    def __init__(self, dynamodb, auth_manager, transactions_table):
        super().__init__(dynamodb, auth_manager)
        self.transactions_table = transactions_table

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        LEVEL: Level 1 (phone verified)
        Search transactions by merchant, amount, date range, or category
        """
        try:
            # Check authorization
            authorized, error, current_level = self.check_auth_level(AUTH_LEVEL_1)
            if not authorized:
                return error

            customer_id, error = self.get_customer_id()
            if error:
                return error

            merchant = content_data.get("merchant")
            min_amount = content_data.get("minAmount")
            max_amount = content_data.get("maxAmount")
            start_date = content_data.get("startDate")
            end_date = content_data.get("endDate")
            category = content_data.get("category")

            # Get all customer transactions
            response = self.transactions_table.scan(FilterExpression=Attr('customerId').eq(customer_id))
            transactions = response.get('Items', [])

            # Apply filters
            filtered = transactions

            if merchant:
                filtered = [t for t in filtered if merchant.lower() in t.get('description', '').lower()]

            if category:
                filtered = [t for t in filtered if t.get('category') == category]

            if min_amount is not None:
                filtered = [t for t in filtered if abs(float(t.get('amount', 0))) >= float(min_amount)]

            if max_amount is not None:
                filtered = [t for t in filtered if abs(float(t.get('amount', 0))) <= float(max_amount)]

            if start_date:
                filtered = [t for t in filtered if t.get('date', '') >= start_date]

            if end_date:
                filtered = [t for t in filtered if t.get('date', '') <= end_date]

            # Sort by date (newest first)
            filtered.sort(key=lambda x: x.get('date', ''), reverse=True)

            # Convert decimals
            filtered = self.convert_decimals(filtered)

            # Audit log
            self.audit_action('SEARCH_TRANSACTIONS', None, AUDIT_RESULT_SUCCESS)

            return {
                "found": True if filtered else False,
                "transactions": filtered,
                "count": len(filtered),
                "filters_applied": {k: v for k, v in content_data.items() if v is not None},
                "message": f"Found {len(filtered)} transactions matching your search."
            }

        except Exception as e:
            self.audit_action('SEARCH_TRANSACTIONS', None, AUDIT_RESULT_FAILURE)
            return {"error": str(e)}


class RequestStatementTool(BaseTool):
    """Request account statement (email, mail, or download)"""

    def __init__(self, dynamodb, auth_manager, accounts_table, customers_table):
        super().__init__(dynamodb, auth_manager)
        self.accounts_table = accounts_table
        self.customers_table = customers_table

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        LEVEL: Level 1 (phone verified)
        Request account statement (email, mail, or download)
        """
        try:
            # Check authorization
            authorized, error, current_level = self.check_auth_level(AUTH_LEVEL_1)
            if not authorized:
                return error

            customer_id, error = self.get_customer_id()
            if error:
                return error

            account_id = content_data.get("accountId")
            delivery_method = content_data.get("deliveryMethod", "email")
            statement_period = content_data.get("period", "current_month")

            if not account_id:
                return {"error": "Account ID is required"}

            # Verify account belongs to customer
            response = self.accounts_table.get_item(Key={'accountId': account_id})
            if 'Item' not in response:
                return {"error": "Account not found"}

            account = response['Item']
            if account['customerId'] != customer_id:
                return {"error": "Account does not belong to customer"}

            # Get customer info for email/address
            customer_response = self.customers_table.get_item(Key={'customerId': customer_id})
            customer = customer_response['Item']

            # Simulate statement generation
            statement_id = f"STMT-{account_id}-{statement_period}"

            result = {
                "success": True,
                "statementId": statement_id,
                "accountId": account_id,
                "period": statement_period,
                "deliveryMethod": delivery_method
            }

            if delivery_method == "email":
                result["message"] = f"Statement for {statement_period} will be sent to {customer.get('email', 'your email')} within 24 hours."
            elif delivery_method == "mail":
                result["message"] = f"Statement for {statement_period} will be mailed to your address on file within 5-7 business days."
            else:  # download
                result["downloadUrl"] = f"https://bank.example.com/statements/{statement_id}.pdf"
                result["message"] = f"Your statement is ready for download."

            # Audit log with PII flag (mailing address)
            self.audit_action('REQUEST_STATEMENT', account_id, AUDIT_RESULT_SUCCESS, pii_accessed=True)

            return result

        except Exception as e:
            self.audit_action('REQUEST_STATEMENT', None, AUDIT_RESULT_FAILURE)
            return {"error": str(e)}
