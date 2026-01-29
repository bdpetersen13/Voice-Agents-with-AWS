"""
Fraud & Dispute Tools
Handles fraud reporting, dispute status checking, and provisional credit education
"""
import datetime
import random
from typing import Dict, Any
from boto3.dynamodb.conditions import Attr
from tools.base_tool import BaseTool
from config.constants import *


class ReportFraudTool(BaseTool):
    """Report suspected fraud on account or card"""

    def __init__(self, dynamodb, auth_manager, cards_table):
        super().__init__(dynamodb, auth_manager)
        self.cards_table = cards_table

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        LEVEL: Level 2 (OTP required)
        Report suspected fraud on account or card
        """
        try:
            authorized, error, _ = self.check_auth_level(AUTH_LEVEL_2)
            if not authorized:
                return error

            customer_id, error = self.get_customer_id()
            if error:
                return error

            fraud_type = content_data.get("fraudType")  # "card", "account", "identity"
            affected_account_id = content_data.get("accountId")
            affected_card_id = content_data.get("cardId")
            description = content_data.get("description", "")

            if not fraud_type:
                return {"error": "fraudType is required"}

            # Create fraud case
            fraud_id = f"FRAUD-{datetime.datetime.now().strftime('%Y%m%d')}-{random.randint(100, 999)}"
            case_number = f"FRAUD-CASE-{random.randint(10000, 99999)}"

            # If card fraud, deactivate card immediately
            if fraud_type == "card" and affected_card_id:
                self.cards_table.update_item(
                    Key={'cardId': affected_card_id},
                    UpdateExpression="SET #status = :deactivated, lostStolen = :true, lostStolenReason = :fraud",
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':deactivated': 'Deactivated',
                        ':true': True,
                        ':fraud': 'Fraud reported'
                    }
                )

            # If account compromise, flag account
            if fraud_type in ["account", "identity"] and affected_account_id:
                # In production, would freeze account and require branch visit
                pass

            # Audit log - critical security event
            self.audit_action('REPORT_FRAUD', fraud_id, AUDIT_RESULT_SUCCESS)

            return {
                "success": True,
                "fraudId": fraud_id,
                "caseNumber": case_number,
                "fraudType": fraud_type,
                "immediateActions": [
                    "Your card has been deactivated" if fraud_type == "card" else "Your account has been flagged",
                    "Fraud investigation initiated",
                    "You will not be held liable for fraudulent charges"
                ],
                "nextSteps": "Our fraud team will contact you within 24 hours. Review your account for any other unauthorized activity. File a police report if identity theft is suspected.",
                "provisionalCredit": "Any fraudulent charges will receive provisional credit within 10 business days.",
                "message": f"Fraud case {case_number} has been opened. Your account security is our top priority. " +
                          ("Your card has been deactivated immediately. " if fraud_type == "card" else "") +
                          "Our fraud investigation team will contact you within 24 hours. You will not be held liable for fraudulent charges."
            }

        except Exception as e:
            self.audit_action('REPORT_FRAUD', None, AUDIT_RESULT_FAILURE)
            return {"error": str(e)}


class CheckDisputeStatusTool(BaseTool):
    """Check status of existing dispute case"""

    def __init__(self, dynamodb, auth_manager, disputes_table):
        super().__init__(dynamodb, auth_manager)
        self.disputes_table = disputes_table

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        LEVEL: Level 1 (phone verified)
        Check status of existing dispute case
        """
        try:
            authorized, error, _ = self.check_auth_level(AUTH_LEVEL_1)
            if not authorized:
                return error

            customer_id, error = self.get_customer_id()
            if error:
                return error

            dispute_id = content_data.get("disputeId")
            case_number = content_data.get("caseNumber")

            # Find dispute
            if dispute_id:
                response = self.disputes_table.get_item(Key={'disputeId': dispute_id})
                if 'Item' not in response:
                    return {"found": False, "message": "Dispute not found"}
                dispute = response['Item']
            elif case_number:
                response = self.disputes_table.scan(FilterExpression=Attr('caseNumber').eq(case_number))
                disputes = response.get('Items', [])
                if not disputes:
                    return {"found": False, "message": "Dispute not found"}
                dispute = disputes[0]
            else:
                return {"error": "disputeId or caseNumber is required"}

            # Verify ownership
            if dispute['customerId'] != customer_id:
                return {"error": "Unauthorized"}

            dispute = self.convert_decimals(dispute)

            self.audit_action('CHECK_DISPUTE_STATUS', dispute['disputeId'], AUDIT_RESULT_SUCCESS)

            return {
                "found": True,
                "dispute": dispute,
                "status": dispute['status'],
                "caseNumber": dispute['caseNumber'],
                "provisionalCreditIssued": dispute.get('provisionalCreditIssued', False),
                "expectedResolution": dispute.get('expectedResolutionDate'),
                "message": f"Dispute case {dispute['caseNumber']} - Status: {dispute['status']}. " +
                          (f"Provisional credit of ${dispute.get('provisionalCreditAmount', '0.00')} issued on {dispute.get('provisionalCreditDate')}" if dispute.get('provisionalCreditIssued') else "Provisional credit pending") +
                          f". Expected resolution: {dispute.get('expectedResolutionDate')}. {dispute.get('nextSteps', '')}"
            }

        except Exception as e:
            self.audit_action('CHECK_DISPUTE_STATUS', None, AUDIT_RESULT_FAILURE)
            return {"error": str(e)}


class ExplainProvisionalCreditTool(BaseTool):
    """Educational tool: Explain provisional credit process during disputes"""

    def __init__(self, dynamodb, auth_manager):
        super().__init__(dynamodb, auth_manager)

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        LEVEL: Level 1 (phone verified)
        Explain provisional credit process during disputes
        """
        try:
            authorized, error, _ = self.check_auth_level(AUTH_LEVEL_1)
            if not authorized:
                return error

            # Educational response about provisional credit
            explanation = {
                "whatIs": "Provisional credit is a temporary credit we give you while investigating a disputed transaction. It's typically the full amount of the disputed charge.",
                "timeline": "You'll receive provisional credit within 10 business days of filing the dispute.",
                "duration": "The credit remains in your account during the investigation (up to 30-45 days for debit cards, 60-90 days for credit cards).",
                "finalResolution": "If we find in your favor, the credit becomes permanent. If the merchant proves the charge was valid, the credit may be reversed.",
                "yourRights": "Under Regulation E (for debit cards) and Fair Credit Billing Act (for credit cards), you have the right to provisional credit while we investigate.",
                "evidence": "You may be asked to provide evidence like receipts, emails, or documentation to support your dispute."
            }

            self.audit_action('EXPLAIN_PROVISIONAL_CREDIT', None, AUDIT_RESULT_SUCCESS)

            return {
                "success": True,
                "explanation": explanation,
                "message": "Provisional credit is a temporary credit we place in your account while investigating a disputed transaction. You'll receive it within 10 business days, and it stays in your account during the investigation. If we find in your favor, it becomes permanent. If the merchant proves the charge was valid, we may reverse the credit. This is your right under federal banking regulations."
            }

        except Exception as e:
            return {"error": str(e)}
