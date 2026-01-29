"""
Session Manager
HIPAA-compliant session management with auto-timeout and isolation

HIPAA Requirements:
- Session timeout after inactivity
- Session isolation (no cross-session data)
- Secure session tokens
- Session termination logging
"""
import datetime
import uuid
import hashlib
from typing import Dict, Any, Optional
from config.constants import SESSION_TIMEOUT_MINUTES, SESSION_WARNING_MINUTES


class SessionManager:
    """HIPAA-compliant session management"""
    
    def __init__(self, dynamodb, sessions_table, audit_logger):
        self.dynamodb = dynamodb
        self.sessions_table = sessions_table
        self.audit_logger = audit_logger
    
    def create_session(self, ip_address: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new HIPAA-compliant session
        
        Returns:
            session: Session object with session_id and expiration
        """
        session_id = f"SES-{uuid.uuid4().hex}"
        created_at = datetime.datetime.utcnow()
        expires_at = created_at + datetime.timedelta(minutes=SESSION_TIMEOUT_MINUTES)
        warning_at = created_at + datetime.timedelta(minutes=SESSION_WARNING_MINUTES)
        
        session = {
            'sessionId': session_id,
            'createdAt': created_at.isoformat() + 'Z',
            'lastActivity': created_at.isoformat() + 'Z',
            'expiresAt': expires_at.isoformat() + 'Z',
            'warningAt': warning_at.isoformat() + 'Z',
            'verified': False,
            'verificationLevel': 0,
            'userId': None,
            'consentGiven': False,
            'ipAddress': ip_address,
            'active': True
        }
        
        self.sessions_table.put_item(Item=session)
        
        # Audit log
        self.audit_logger.log_session_event(
            session_id=session_id,
            event='SESSION_CREATED'
        )
        
        return session
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session and check if still valid"""
        response = self.sessions_table.get_item(Key={'sessionId': session_id})
        
        if 'Item' not in response:
            return None
        
        session = response['Item']
        
        # Check if expired
        expires_at = datetime.datetime.fromisoformat(session['expiresAt'].replace('Z', ''))
        if datetime.datetime.utcnow() > expires_at:
            self.terminate_session(session_id, reason='TIMEOUT')
            return None
        
        return session
    
    def update_activity(self, session_id: str) -> bool:
        """Update last activity timestamp (extends session)"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        now = datetime.datetime.utcnow()
        new_expires_at = now + datetime.timedelta(minutes=SESSION_TIMEOUT_MINUTES)
        new_warning_at = now + datetime.timedelta(minutes=SESSION_WARNING_MINUTES)
        
        self.sessions_table.update_item(
            Key={'sessionId': session_id},
            UpdateExpression="SET lastActivity = :la, expiresAt = :ea, warningAt = :wa",
            ExpressionAttributeValues={
                ':la': now.isoformat() + 'Z',
                ':ea': new_expires_at.isoformat() + 'Z',
                ':wa': new_warning_at.isoformat() + 'Z'
            }
        )
        
        return True
    
    def set_verified(
        self,
        session_id: str,
        user_id: str,
        verification_level: int
    ) -> bool:
        """Mark session as verified"""
        self.sessions_table.update_item(
            Key={'sessionId': session_id},
            UpdateExpression="SET verified = :v, userId = :u, verificationLevel = :vl",
            ExpressionAttributeValues={
                ':v': True,
                ':u': user_id,
                ':vl': verification_level
            }
        )
        
        # Audit log
        self.audit_logger.log_session_event(
            session_id=session_id,
            event='SESSION_VERIFIED',
            user_id=user_id
        )
        
        return True
    
    def set_consent(self, session_id: str, consent_given: bool) -> bool:
        """Record consent for this session"""
        self.sessions_table.update_item(
            Key={'sessionId': session_id},
            UpdateExpression="SET consentGiven = :c",
            ExpressionAttributeValues={
                ':c': consent_given
            }
        )
        
        return True
    
    def check_warning(self, session_id: str) -> bool:
        """Check if session should show timeout warning"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        warning_at = datetime.datetime.fromisoformat(session['warningAt'].replace('Z', ''))
        return datetime.datetime.utcnow() > warning_at
    
    def terminate_session(self, session_id: str, reason: str = 'USER_INITIATED') -> bool:
        """Terminate session and log"""
        self.sessions_table.update_item(
            Key={'sessionId': session_id},
            UpdateExpression="SET active = :a, terminatedAt = :t, terminationReason = :r",
            ExpressionAttributeValues={
                ':a': False,
                ':t': datetime.datetime.utcnow().isoformat() + 'Z',
                ':r': reason
            }
        )
        
        # Audit log
        session = self.sessions_table.get_item(Key={'sessionId': session_id}).get('Item')
        self.audit_logger.log_session_event(
            session_id=session_id,
            event='SESSION_TERMINATED',
            user_id=session.get('userId') if session else None
        )
        
        return True
    
    def requires_verification(self, session_id: str, required_level: int = 1) -> bool:
        """Check if session has required verification level"""
        session = self.get_session(session_id)
        if not session:
            return True
        
        return session.get('verificationLevel', 0) < required_level
    
    def requires_consent(self, session_id: str) -> bool:
        """Check if session has consent"""
        session = self.get_session(session_id)
        if not session:
            return True
        
        return not session.get('consentGiven', False)
