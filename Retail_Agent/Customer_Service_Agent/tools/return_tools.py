"""
Return Tools
Tools for verifying and processing item returns
"""
import datetime
import random
from decimal import Decimal
from typing import Dict, Any
from tools.base_tool import BaseTool


class VerifyReturnItemTool(BaseTool):
    """Simulate computer vision verification of item on return shelf"""

    def __init__(self, dynamodb, transactions_table):
        super().__init__(dynamodb)
        self.transactions_table = transactions_table
        # Simulated CV system state (in production, this would be a separate service)
        self.cv_last_scan = None

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate computer vision verification of item on return shelf.
        In production, this would integrate with CV service and weight sensor.

        Returns item identification and weight match status.
        """
        try:
            transaction_id = content_data.get("transactionId")
            expected_sku = content_data.get("expectedSku")  # Optional: if member told us what they're returning

            if not transaction_id:
                return {"error": "transactionId is required to verify return item."}

            # Simulate CV scan (in production, this would call CV API)
            # For demo, we'll return a successful match for items in the transaction

            response = self.transactions_table.get_item(Key={'transactionId': transaction_id})
            if 'Item' not in response:
                return {"verified": False, "message": "Transaction not found."}

            txn = response['Item']
            items = txn.get('items', [])

            # Simulate CV detecting the first returnable item
            # In production: CV would analyze image, identify SKU, measure weight
            returnable_items = [item for item in items if item.get('returnable', False)]

            if not returnable_items:
                return {
                    "verified": False,
                    "message": "No returnable items found in this transaction."
                }

            # If specific SKU expected, find it
            if expected_sku:
                detected_item = next((item for item in returnable_items if item.get('sku') == expected_sku), None)
            else:
                detected_item = returnable_items[0]  # First returnable item

            if not detected_item:
                return {
                    "verified": False,
                    "message": f"Item {expected_sku} not found or not returnable in this transaction."
                }

            # Simulate weight verification (in production, compare sensor reading to expected weight)
            weight_match = True  # In production: abs(sensor_weight - expected_weight) < tolerance

            # Store for next step (initiate return)
            self.cv_last_scan = {
                "transactionId": transaction_id,
                "item": detected_item,
                "weightMatch": weight_match,
                "timestamp": datetime.datetime.now().isoformat()
            }

            return {
                "verified": True,
                "itemDetected": {
                    "sku": detected_item.get('sku'),
                    "name": detected_item.get('name'),
                    "quantity": detected_item.get('quantity'),
                    "originalPrice": str(detected_item.get('unitPrice', '0.00'))
                },
                "weightMatch": weight_match,
                "message": f"Item verified: {detected_item.get('name')}. Weight matches expected. Ready to process return."
            }

        except Exception as e:
            return {"error": str(e)}


class InitiateReturnTool(BaseTool):
    """Process a return after CV verification"""

    def __init__(self, dynamodb, transactions_table, returns_table):
        super().__init__(dynamodb)
        self.transactions_table = transactions_table
        self.returns_table = returns_table

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a return after CV verification.
        Creates return record and calculates refund.
        """
        try:
            member_id = content_data.get("memberId")
            transaction_id = content_data.get("transactionId")
            sku = content_data.get("sku")
            quantity = content_data.get("quantity", 1)
            reason = content_data.get("reason", "Customer requested return")

            if not all([member_id, transaction_id, sku]):
                return {"error": "memberId, transactionId, and sku are required."}

            # Verify transaction exists and belongs to member
            response = self.transactions_table.get_item(Key={'transactionId': transaction_id})
            if 'Item' not in response:
                return {"error": "Transaction not found."}

            txn = response['Item']
            if txn.get('memberId') != member_id:
                return {"error": "Transaction does not belong to this member."}

            # Find the item
            items = txn.get('items', [])
            item_to_return = next((item for item in items if item.get('sku') == sku), None)

            if not item_to_return:
                return {"error": f"Item {sku} not found in transaction."}

            if not item_to_return.get('returnable', False):
                return {
                    "success": False,
                    "message": f"{item_to_return.get('name')} is not eligible for return (perishable or restricted item)."
                }

            # Check return window (90 days)
            txn_date = datetime.datetime.strptime(txn.get('date'), '%Y-%m-%d').date()
            today = datetime.date.today()
            days_since_purchase = (today - txn_date).days

            if days_since_purchase > 90:
                return {
                    "success": False,
                    "message": f"Return window expired. Item was purchased {days_since_purchase} days ago (90-day limit)."
                }

            # Calculate refund
            unit_price = float(item_to_return.get('unitPrice', 0))
            refund_amount = Decimal(str(unit_price * quantity))

            # Generate return ID
            return_id = f"RET-{datetime.date.today().strftime('%Y%m%d')}-{random.randint(10000, 99999)}"

            # Create return record
            self.returns_table.put_item(Item={
                'returnId': return_id,
                'transactionId': transaction_id,
                'memberId': member_id,
                'returnDate': today.strftime('%Y-%m-%d'),
                'returnedItems': [
                    {
                        'sku': sku,
                        'name': item_to_return.get('name'),
                        'quantity': quantity,
                        'refundAmount': refund_amount,
                        'reason': reason
                    }
                ],
                'refundTotal': refund_amount,
                'refundMethod': txn.get('paymentMethod'),
                'status': 'Processed'
            })

            return {
                "success": True,
                "returnId": return_id,
                "refundAmount": str(refund_amount),
                "refundMethod": txn.get('paymentMethod'),
                "message": f"Return processed successfully. Refund of ${refund_amount} will be credited to {txn.get('paymentMethod')} within 3-5 business days. Your return ID is {return_id}."
            }

        except Exception as e:
            return {"error": str(e)}
