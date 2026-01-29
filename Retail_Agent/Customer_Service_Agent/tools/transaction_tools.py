"""
Transaction Tools
Tools for looking up and processing transaction issues
"""
import datetime
import random
from decimal import Decimal
from typing import Dict, Any
from boto3.dynamodb.conditions import Attr
from tools.base_tool import BaseTool


class LookupTransactionTool(BaseTool):
    """Look up recent transactions or a specific transaction by ID"""

    def __init__(self, dynamodb, transactions_table):
        super().__init__(dynamodb)
        self.transactions_table = transactions_table

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Look up recent transactions or a specific transaction by ID.
        Supports filtering by date range.
        """
        try:
            member_id = content_data.get("memberId")
            transaction_id = content_data.get("transactionId")
            days_back = content_data.get("daysBack", 30)  # Default to last 30 days

            if not member_id and not transaction_id:
                return {"error": "Either memberId or transactionId is required."}

            # Specific transaction lookup
            if transaction_id:
                response = self.transactions_table.get_item(Key={'transactionId': transaction_id})
                if 'Item' not in response:
                    return {"found": False, "message": "Transaction not found."}

                txn = response['Item']
                # Convert Decimals to strings
                txn = self.convert_decimals(txn)
                return {
                    "found": True,
                    "transactions": [txn],
                    "message": f"Found transaction {transaction_id} from {txn['date']}."
                }

            # Recent transactions by member
            today = datetime.date.today()
            cutoff_date = (today - datetime.timedelta(days=days_back)).strftime('%Y-%m-%d')

            filter_expression = Attr('memberId').eq(member_id) & Attr('date').gte(cutoff_date)
            response = self.transactions_table.scan(FilterExpression=filter_expression)
            items = response.get('Items', [])

            if not items:
                return {
                    "found": False,
                    "message": f"No transactions found in the last {days_back} days."
                }

            # Sort by date (most recent first)
            items.sort(key=lambda x: x.get('date', ''), reverse=True)
            items = [self.convert_decimals(item) for item in items]

            return {
                "found": True,
                "transactions": items[:10],  # Return max 10 most recent
                "count": len(items),
                "message": f"Found {len(items)} transaction(s) in the last {days_back} days."
            }

        except Exception as e:
            return {"error": str(e)}


class ProcessTransactionIssueTool(BaseTool):
    """Handle checkout errors like double-scans, missed items, price adjustments"""

    def __init__(self, dynamodb, transactions_table, service_requests_table):
        super().__init__(dynamodb)
        self.transactions_table = transactions_table
        self.service_requests_table = service_requests_table

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle checkout errors like double-scans, missed items, price adjustments.
        Creates adjustment and issues refund/credit.
        """
        try:
            member_id = content_data.get("memberId")
            transaction_id = content_data.get("transactionId")
            issue_type = content_data.get("issueType")  # "double_scan", "missed_item", "wrong_price"
            item_sku = content_data.get("itemSku")
            adjustment_amount = content_data.get("adjustmentAmount")  # For refunds
            description = content_data.get("description", "Transaction adjustment")

            if not all([member_id, transaction_id, issue_type]):
                return {"error": "memberId, transactionId, and issueType are required."}

            # Verify transaction
            response = self.transactions_table.get_item(Key={'transactionId': transaction_id})
            if 'Item' not in response:
                return {"error": "Transaction not found."}

            txn = response['Item']
            if txn.get('memberId') != member_id:
                return {"error": "Transaction does not belong to this member."}

            # Generate service request for tracking
            request_id = f"REQ-{datetime.date.today().strftime('%Y%m%d')}-{random.randint(10000, 99999)}"

            self.service_requests_table.put_item(Item={
                'requestId': request_id,
                'memberId': member_id,
                'requestType': 'Transaction Issue',
                'description': f"{issue_type}: {description} (Transaction: {transaction_id})",
                'status': 'Resolved',
                'createdDate': datetime.datetime.now().isoformat(),
                'resolvedDate': datetime.datetime.now().isoformat(),
                'resolution': f"Adjustment of ${adjustment_amount} issued."
            })

            refund_amount = Decimal(str(adjustment_amount)) if adjustment_amount else Decimal('0.00')

            return {
                "success": True,
                "requestId": request_id,
                "adjustmentAmount": str(refund_amount),
                "message": f"Transaction issue resolved. Refund of ${refund_amount} will be credited to {txn.get('paymentMethod')} within 3-5 business days. Reference: {request_id}"
            }

        except Exception as e:
            return {"error": str(e)}
