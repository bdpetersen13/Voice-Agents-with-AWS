"""
Card Services Tools
Handles card management: lost/stolen reports, freeze/unfreeze, disputes, merchant clarification
"""
import datetime
import random
from typing import Dict, Any
from boto3.dynamodb.conditions import Attr
from tools.base_tool import BaseTool
from config.constants import *


class ReportLostCardTool(BaseTool):
    """Report card as lost or stolen - immediately deactivates card"""

    def __init__(self, dynamodb, auth_manager, cards_table):
        super().__init__(dynamodb, auth_manager)
        self.cards_table = cards_table

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        LEVEL: Level 1 (phone verified)
        Report card as lost or stolen - immediately deactivates card
        """
        try:
            authorized, error, _ = self.check_auth_level(AUTH_LEVEL_1)
            if not authorized:
                return error

            customer_id, error = self.get_customer_id()
            if error:
                return error

            card_id = content_data.get("cardId")
            last_four = content_data.get("lastFour")
            reason = content_data.get("reason", "Lost")

            # Find card
            if card_id:
                response = self.cards_table.get_item(Key={'cardId': card_id})
                if 'Item' not in response:
                    return {"found": False, "message": "Card not found"}
                card = response['Item']
            elif last_four:
                response = self.cards_table.scan(
                    FilterExpression=Attr('customerId').eq(customer_id) & Attr('cardNumber').contains(last_four)
                )
                cards = response.get('Items', [])
                if not cards:
                    return {"found": False, "message": "No card found with those last 4 digits"}
                card = cards[0]
                card_id = card['cardId']
            else:
                return {"error": "Either cardId or lastFour is required"}

            if card['customerId'] != customer_id:
                return {"error": "Unauthorized"}

            # Deactivate card
            self.cards_table.update_item(
                Key={'cardId': card_id},
                UpdateExpression="SET #status = :deactivated, lostStolen = :true, lostStolenDate = :now, lostStolenReason = :reason",
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':deactivated': 'Deactivated',
                    ':true': True,
                    ':now': datetime.datetime.now().isoformat(),
                    ':reason': reason
                }
            )

            self.audit_action('REPORT_LOST_CARD', card_id, AUDIT_RESULT_SUCCESS)

            return {
                "success": True,
                "cardId": card_id,
                "cardNumber": card['cardNumber'],
                "status": "Deactivated",
                "message": f"Your card ending in {card['cardNumber'][-4:]} has been deactivated for security. No further transactions can be made on this card. Would you like to order a replacement card? (This requires additional authentication)"
            }

        except Exception as e:
            self.audit_action('REPORT_LOST_CARD', None, AUDIT_RESULT_FAILURE)
            return {"error": str(e)}


class FreezeCardTool(BaseTool):
    """Temporarily freeze card (can be unfrozen by customer)"""

    def __init__(self, dynamodb, auth_manager, cards_table):
        super().__init__(dynamodb, auth_manager)
        self.cards_table = cards_table

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        LEVEL: Level 1 (phone verified)
        Temporarily freeze card
        """
        try:
            authorized, error, _ = self.check_auth_level(AUTH_LEVEL_1)
            if not authorized:
                return error

            customer_id, error = self.get_customer_id()
            if error:
                return error

            card_id = content_data.get("cardId")
            last_four = content_data.get("lastFour")

            # Find card
            if card_id:
                response = self.cards_table.get_item(Key={'cardId': card_id})
                if 'Item' not in response:
                    return {"found": False, "message": "Card not found"}
                card = response['Item']
            elif last_four:
                response = self.cards_table.scan(
                    FilterExpression=Attr('customerId').eq(customer_id) & Attr('cardNumber').contains(last_four)
                )
                cards = response.get('Items', [])
                if not cards:
                    return {"found": False, "message": "No card found"}
                card = cards[0]
                card_id = card['cardId']
            else:
                return {"error": "Either cardId or lastFour is required"}

            if card['customerId'] != customer_id:
                return {"error": "Unauthorized"}

            if card.get('frozen', False):
                return {"success": False, "message": "This card is already frozen"}

            # Freeze card
            self.cards_table.update_item(
                Key={'cardId': card_id},
                UpdateExpression="SET frozen = :true, frozenDate = :now, frozenReason = :reason",
                ExpressionAttributeValues={
                    ':true': True,
                    ':now': datetime.datetime.now().isoformat(),
                    ':reason': 'Customer request - temporary freeze'
                }
            )

            self.audit_action('FREEZE_CARD', card_id, AUDIT_RESULT_SUCCESS)

            return {
                "success": True,
                "cardId": card_id,
                "cardNumber": card['cardNumber'],
                "frozen": True,
                "message": f"Your card ending in {card['cardNumber'][-4:]} is now frozen. No transactions can be made until you unfreeze it. You can unfreeze it anytime by calling us."
            }

        except Exception as e:
            self.audit_action('FREEZE_CARD', None, AUDIT_RESULT_FAILURE)
            return {"error": str(e)}


class UnfreezeCardTool(BaseTool):
    """Unfreeze previously frozen card"""

    def __init__(self, dynamodb, auth_manager, cards_table):
        super().__init__(dynamodb, auth_manager)
        self.cards_table = cards_table

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        LEVEL: Level 2 (OTP required for security)
        Unfreeze previously frozen card
        """
        try:
            authorized, error, _ = self.check_auth_level(AUTH_LEVEL_2)
            if not authorized:
                return error

            customer_id, error = self.get_customer_id()
            if error:
                return error

            card_id = content_data.get("cardId")
            last_four = content_data.get("lastFour")

            # Find card
            if card_id:
                response = self.cards_table.get_item(Key={'cardId': card_id})
                if 'Item' not in response:
                    return {"found": False, "message": "Card not found"}
                card = response['Item']
            elif last_four:
                response = self.cards_table.scan(
                    FilterExpression=Attr('customerId').eq(customer_id) & Attr('cardNumber').contains(last_four)
                )
                cards = response.get('Items', [])
                if not cards:
                    return {"found": False, "message": "No card found"}
                card = cards[0]
                card_id = card['cardId']
            else:
                return {"error": "Either cardId or lastFour is required"}

            if card['customerId'] != customer_id:
                return {"error": "Unauthorized"}

            if not card.get('frozen', False):
                return {"success": False, "message": "This card is not frozen"}

            if card.get('lostStolen', False):
                return {"success": False, "message": "This card was reported lost/stolen and cannot be unfrozen. You need to order a replacement card."}

            # Unfreeze card
            self.cards_table.update_item(
                Key={'cardId': card_id},
                UpdateExpression="SET frozen = :false, unfrozenDate = :now",
                ExpressionAttributeValues={
                    ':false': False,
                    ':now': datetime.datetime.now().isoformat()
                }
            )

            self.audit_action('UNFREEZE_CARD', card_id, AUDIT_RESULT_SUCCESS)

            return {
                "success": True,
                "cardId": card_id,
                "cardNumber": card['cardNumber'],
                "frozen": False,
                "message": f"Your card ending in {card['cardNumber'][-4:]} has been unfrozen. You can now use it for transactions."
            }

        except Exception as e:
            self.audit_action('UNFREEZE_CARD', None, AUDIT_RESULT_FAILURE)
            return {"error": str(e)}


class CheckReplacementStatusTool(BaseTool):
    """Check status of replacement card order"""

    def __init__(self, dynamodb, auth_manager, cards_table):
        super().__init__(dynamodb, auth_manager)
        self.cards_table = cards_table

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        LEVEL: Level 1 (phone verified)
        Check status of replacement card order
        """
        try:
            authorized, error, _ = self.check_auth_level(AUTH_LEVEL_1)
            if not authorized:
                return error

            customer_id, error = self.get_customer_id()
            if error:
                return error

            card_id = content_data.get("cardId")

            response = self.cards_table.get_item(Key={'cardId': card_id})
            if 'Item' not in response:
                return {"found": False, "message": "Card not found"}

            card = response['Item']

            if card['customerId'] != customer_id:
                return {"error": "Unauthorized"}

            replacement_status = card.get('replacementStatus')

            if not replacement_status:
                return {
                    "found": True,
                    "hasReplacement": False,
                    "message": "No replacement card has been ordered for this card."
                }

            self.audit_action('CHECK_REPLACEMENT_STATUS', card_id, AUDIT_RESULT_SUCCESS)

            return {
                "found": True,
                "hasReplacement": True,
                "replacementStatus": replacement_status,
                "cardId": card_id,
                "message": f"Your replacement card status: {replacement_status}. Expected delivery: 7-10 business days from order date."
            }

        except Exception as e:
            self.audit_action('CHECK_REPLACEMENT_STATUS', None, AUDIT_RESULT_FAILURE)
            return {"error": str(e)}


class DisputeChargeTool(BaseTool):
    """Dispute a transaction/charge"""

    def __init__(self, dynamodb, auth_manager, transactions_table, disputes_table):
        super().__init__(dynamodb, auth_manager)
        self.transactions_table = transactions_table
        self.disputes_table = disputes_table

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        LEVEL: Level 2 (OTP required)
        Dispute a transaction/charge
        """
        try:
            authorized, error, _ = self.check_auth_level(AUTH_LEVEL_2)
            if not authorized:
                return error

            customer_id, error = self.get_customer_id()
            if error:
                return error

            transaction_id = content_data.get("transactionId")
            dispute_reason = content_data.get("reason")
            description = content_data.get("description", "")

            if not transaction_id or not dispute_reason:
                return {"error": "transactionId and reason are required"}

            # Get transaction
            response = self.transactions_table.get_item(Key={'transactionId': transaction_id})
            if 'Item' not in response:
                return {"found": False, "message": "Transaction not found"}

            transaction = response['Item']

            if transaction['customerId'] != customer_id:
                return {"error": "Unauthorized"}

            # Create dispute case
            dispute_id = f"DISP-{datetime.datetime.now().strftime('%Y%m%d')}-{random.randint(100, 999)}"
            case_number = f"CASE-{random.randint(10000, 99999)}"
            expected_resolution = (datetime.date.today() + datetime.timedelta(days=30)).strftime('%Y-%m-%d')

            dispute = {
                'disputeId': dispute_id,
                'customerId': customer_id,
                'accountId': transaction['accountId'],
                'transactionId': transaction_id,
                'amount': transaction['amount'],
                'merchant': transaction.get('merchant', transaction.get('description')),
                'disputeReason': dispute_reason,
                'description': description,
                'status': 'Filed',
                'filedDate': datetime.datetime.now().isoformat(),
                'expectedResolutionDate': expected_resolution,
                'provisionalCreditIssued': False,
                'caseNumber': case_number,
                'nextSteps': 'Bank will contact merchant within 5 business days. You may be contacted for additional information.',
                'timeline': '10 business days for provisional credit, 30 days total for investigation',
                'updatedAt': datetime.datetime.now().isoformat()
            }

            self.disputes_table.put_item(Item=dispute)

            self.audit_action('DISPUTE_CHARGE', transaction_id, AUDIT_RESULT_SUCCESS)

            return {
                "success": True,
                "disputeId": dispute_id,
                "caseNumber": case_number,
                "amount": str(transaction['amount']),
                "merchant": transaction.get('merchant'),
                "status": "Filed",
                "expectedResolution": expected_resolution,
                "message": f"Your dispute has been filed. Case number: {case_number}. We'll investigate this charge and contact the merchant. You should receive provisional credit within 10 business days, and final resolution within 30 days. You may be contacted for additional information."
            }

        except Exception as e:
            self.audit_action('DISPUTE_CHARGE', None, AUDIT_RESULT_FAILURE)
            return {"error": str(e)}


class ClarifyMerchantTool(BaseTool):
    """Clarify what a merchant code means"""

    def __init__(self, dynamodb, auth_manager, transactions_table):
        super().__init__(dynamodb, auth_manager)
        self.transactions_table = transactions_table

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        LEVEL: Level 1 (phone verified)
        Clarify what a merchant code means (e.g., "What is SQ*ABC123?")
        """
        try:
            authorized, error, _ = self.check_auth_level(AUTH_LEVEL_1)
            if not authorized:
                return error

            merchant_code = content_data.get("merchantCode")
            transaction_id = content_data.get("transactionId")

            if transaction_id:
                response = self.transactions_table.get_item(Key={'transactionId': transaction_id})
                if 'Item' not in response:
                    return {"found": False, "message": "Transaction not found"}
                transaction = response['Item']
                merchant_code = transaction.get('merchantCode', transaction.get('description'))

            if not merchant_code:
                return {"error": "merchantCode or transactionId is required"}

            # Merchant code explanations
            merchant_explanations = {
                'SQ*': 'Square payment processor - used by many small businesses',
                'TST*': 'Toast payment processor - commonly used by restaurants',
                'AMZN': 'Amazon.com',
                'PAYPAL': 'PayPal payment',
                'VENMO': 'Venmo payment',
                'UBER': 'Uber ride or Uber Eats',
                'DOORDASH': 'DoorDash food delivery'
            }

            # Find matching explanation
            explanation = None
            actual_merchant = None
            for prefix, desc in merchant_explanations.items():
                if merchant_code.upper().startswith(prefix):
                    explanation = desc
                    if transaction_id:
                        actual_merchant = transaction.get('merchant', 'Unknown business')
                    break

            if not explanation:
                explanation = "This appears to be a standard merchant code. The specific business name may vary."

            self.audit_action('CLARIFY_MERCHANT', merchant_code, AUDIT_RESULT_SUCCESS)

            return {
                "found": True,
                "merchantCode": merchant_code,
                "explanation": explanation,
                "actualMerchant": actual_merchant,
                "message": f"{merchant_code} - {explanation}" + (f" In this case: {actual_merchant}" if actual_merchant else "")
            }

        except Exception as e:
            self.audit_action('CLARIFY_MERCHANT', None, AUDIT_RESULT_FAILURE)
            return {"error": str(e)}
