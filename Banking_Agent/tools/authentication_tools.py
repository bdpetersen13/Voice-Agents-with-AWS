"""
Authentication Tools
Handles user authentication, OTP verification, and step-up authentication
"""
from typing import Dict, Any
from tools.base_tool import BaseTool
from config.constants import *


class AuthenticateTool(BaseTool):
    """Authenticate user with phone number - creates session at Level 1"""

    def __init__(self, dynamodb, auth_manager, customers_table):
        super().__init__(dynamodb, auth_manager)
        self.customers_table = customers_table

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        LEVEL: Public (no auth required)
        Authenticate user with phone number - creates session at Level 1
        """
        try:
            phone = content_data.get("phone")

            if not phone:
                return {"error": "Phone number is required"}

            # Create authentication session
            session = self.auth_manager.create_session(phone)

            if not session:
                return {
                    "authenticated": False,
                    "message": "No account found with that phone number. Please verify the number or visit a branch."
                }

            # Set current session
            self.current_session_id = session['sessionId']

            # Record call disclosure consent
            self.auth_manager.record_consent(
                session['sessionId'],
                'call_recording',
                'This call may be recorded for quality assurance and regulatory compliance purposes.',
                True
            )

            # Get customer info
            response = self.customers_table.get_item(Key={'customerId': session['customerId']})
            customer = response['Item']

            return {
                "authenticated": True,
                "sessionId": session['sessionId'],
                "authLevel": AUTH_LEVEL_1,
                "customerName": customer['name'],
                "message": f"Welcome back, {customer['name']}! I've verified your identity with your phone number. You now have access to basic account information.",
                "mfaEnabled": customer.get('mfaEnabled', False),
                "requiresStepUp": "Some operations may require additional authentication."
            }

        except Exception as e:
            return {"error": str(e)}


class VerifyOtpTool(BaseTool):
    """Verify OTP code sent to customer - upgrades to Level 2"""

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        LEVEL: Level 1 required
        Verify OTP code sent to customer - upgrades to Level 2
        """
        try:
            otp_code = content_data.get("otpCode") or content_data.get("otp")

            # Check session
            has_session, error = self.check_session()
            if not has_session:
                return error

            if not otp_code:
                return {"error": "OTP code is required"}

            # Verify OTP
            result = self.auth_manager.verify_otp(self.current_session_id, otp_code)

            if result['success']:
                return {
                    **result,
                    "authLevel": AUTH_LEVEL_2,
                    "message": "OTP verified successfully! You now have access to transfers, full account details, and card management."
                }
            else:
                return result

        except Exception as e:
            return {"error": str(e)}


class StepUpAuthenticationTool(BaseTool):
    """Complete knowledge-based authentication - upgrades to Level 3"""

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        LEVEL: Level 2 required
        Complete knowledge-based authentication - upgrades to Level 3
        """
        try:
            # Check session
            has_session, error = self.check_session()
            if not has_session:
                return error

            action = content_data.get("action")  # "get_question" or "verify_answer"

            if action == "get_question":
                # Get security question
                question = self.auth_manager.ask_knowledge_question(self.current_session_id)
                if not question:
                    return {"error": "Unable to retrieve security question"}

                return {
                    "success": True,
                    "question": question['question'],
                    "questionType": question['questionType'],
                    "message": "To complete high-security authentication, please answer this security question."
                }

            elif action == "verify_answer":
                question_type = content_data.get("questionType")
                answer = content_data.get("answer")

                if not question_type or not answer:
                    return {"error": "Question type and answer are required"}

                # Verify answer
                result = self.auth_manager.verify_knowledge_answer(
                    self.current_session_id,
                    question_type,
                    answer
                )

                if result['success']:
                    return {
                        **result,
                        "authLevel": AUTH_LEVEL_3,
                        "message": "Security verification complete! You now have full access to all banking operations including wire transfers and external account management."
                    }
                else:
                    return result
            else:
                return {"error": "Invalid action. Use 'get_question' or 'verify_answer'"}

        except Exception as e:
            return {"error": str(e)}
