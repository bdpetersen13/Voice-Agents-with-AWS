"""
Base Tool Class
Provides common functionality for all banking tools
"""
from typing import Dict, Any, Tuple, Optional
from decimal import Decimal
from config.constants import *
from core.authentication import BankingAuthenticationManager


class BaseTool:
    """Base class for all banking tools with common patterns"""

    def __init__(self, dynamodb, auth_manager: BankingAuthenticationManager, current_session_id: Optional[str] = None):
        """
        Initialize base tool

        Args:
            dynamodb: DynamoDB resource
            auth_manager: Authentication manager instance
            current_session_id: Current session ID (will be set by tool processor)
        """
        self.dynamodb = dynamodb
        self.auth_manager = auth_manager
        self.current_session_id = current_session_id

    def set_session_id(self, session_id: str):
        """Set the current session ID"""
        self.current_session_id = session_id

    def check_session(self) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if there is an active session

        Returns:
            Tuple of (success, error_dict or None)
        """
        if not self.current_session_id:
            return False, {"error": "No active session. Please authenticate first."}
        return True, None

    def check_auth_level(self, required_level: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Check if session has required authentication level

        Args:
            required_level: Required auth level (AUTH_LEVEL_1, AUTH_LEVEL_2, AUTH_LEVEL_3)

        Returns:
            Tuple of (authorized, error_dict or None, current_level)
        """
        if not self.current_session_id:
            return False, {"error": "No active session. Please authenticate first."}, None

        authorized, message, current_level = self.auth_manager.check_auth_level(
            self.current_session_id, required_level
        )

        if not authorized:
            # Auto-send OTP if stepping up from Level 1 to Level 2
            if required_level == AUTH_LEVEL_2 and current_level == AUTH_LEVEL_1:
                otp_result = self.auth_manager.send_otp(self.current_session_id)
                return False, {
                    "authorized": False,
                    "message": message + " " + otp_result['message'],
                    "authLevel": current_level,
                    "nextStep": "verify_otp"
                }, current_level

            return False, {
                "authorized": False,
                "message": message,
                "authLevel": current_level,
                "requiresStepUp": True
            }, current_level

        return True, None, current_level

    def get_customer_id(self) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        Get customer ID from current session

        Returns:
            Tuple of (customer_id or None, error_dict or None)
        """
        if not self.current_session_id:
            return None, {"error": "No active session. Please authenticate first."}

        session = self.auth_manager.get_session(self.current_session_id)
        if not session:
            return None, {"error": "Session not found or expired. Please authenticate again."}

        return session['customerId'], None

    def audit_action(self, action: str, resource: Optional[str], result: str, pii_accessed: bool = False):
        """
        Log action to audit trail

        Args:
            action: Action name (e.g., 'CHECK_BALANCE')
            resource: Resource ID (e.g., account ID)
            result: Result status (AUDIT_RESULT_SUCCESS or AUDIT_RESULT_FAILURE)
            pii_accessed: Whether PII was accessed
        """
        if self.current_session_id:
            session = self.auth_manager.get_session(self.current_session_id)
            if session:
                self.auth_manager._audit_log(
                    self.current_session_id,
                    session['customerId'],
                    action,
                    resource,
                    result,
                    session['authLevel'],
                    pii_accessed
                )

    def convert_decimals(self, obj: Any) -> Any:
        """
        Convert DynamoDB Decimal types to strings for JSON serialization

        Args:
            obj: Object to convert (can be dict, list, or Decimal)

        Returns:
            Converted object with Decimals as strings
        """
        if isinstance(obj, list):
            return [self.convert_decimals(i) for i in obj]
        elif isinstance(obj, dict):
            return {k: self.convert_decimals(v) for k, v in obj.items()}
        elif isinstance(obj, Decimal):
            return str(obj)
        else:
            return obj

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool logic. Must be implemented by subclasses.

        Args:
            content_data: Tool input parameters

        Returns:
            Tool execution result
        """
        raise NotImplementedError("Subclasses must implement execute()")
