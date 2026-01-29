"""
Audit Logger
HIPAA-compliant audit logging for all PHI access and actions

HIPAA Requirements:
- Log all access to PHI
- Log all modifications to PHI
- Log authentication attempts
- Log consent capture
- Tamper-proof logs
- Minimum 6-year retention
"""
import datetime
import uuid
import hashlib
import json
from typing import Dict, Any, Optional


class AuditLogger:
    """HIPAA-compliant audit logging"""
    
    def __init__(self, dynamodb, audit_table):
        self.dynamodb = dynamodb
        self.audit_table = audit_table
    
    def log_event(
        self,
        event_type: str,
        user_id: Optional[str],
        session_id: str,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        phi_accessed: bool = False,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> str:
        """
        Log an audit event
        
        Args:
            event_type: Type of event (AUTH, PHI_ACCESS, APPOINTMENT, CONSENT, etc.)
            user_id: Patient ID or user identifier
            session_id: Session identifier
            action: Action performed (CREATE, READ, UPDATE, DELETE, VERIFY, etc.)
            resource_type: Type of resource accessed
            resource_id: ID of resource accessed
            phi_accessed: Whether PHI was accessed
            success: Whether action succeeded
            details: Additional details (sanitized, no PHI)
            ip_address: IP address of request
            
        Returns:
            audit_log_id: Unique audit log ID
        """
        audit_log_id = f"AUDIT-{datetime.datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:12]}"
        timestamp = datetime.datetime.utcnow().isoformat() + 'Z'
        
        # Create tamper-detection hash
        hash_data = f"{audit_log_id}{timestamp}{event_type}{action}{user_id}{session_id}"
        tamper_hash = hashlib.sha256(hash_data.encode()).hexdigest()
        
        audit_entry = {
            'auditLogId': audit_log_id,
            'timestamp': timestamp,
            'eventType': event_type,
            'userId': user_id or 'ANONYMOUS',
            'sessionId': session_id,
            'action': action,
            'resourceType': resource_type,
            'resourceId': resource_id,
            'phiAccessed': phi_accessed,
            'success': success,
            'ipAddress': ip_address,
            'details': json.dumps(details) if details else None,
            'tamperHash': tamper_hash,
            'retentionDate': (datetime.datetime.utcnow() + datetime.timedelta(days=365*6)).isoformat() + 'Z'  # 6 years
        }
        
        # Write to audit log table
        self.audit_table.put_item(Item=audit_entry)
        
        return audit_log_id
    
    def log_phi_access(
        self,
        user_id: str,
        session_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        reason: str
    ) -> str:
        """Log PHI access (HIPAA required)"""
        return self.log_event(
            event_type='PHI_ACCESS',
            user_id=user_id,
            session_id=session_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            phi_accessed=True,
            success=True,
            details={'reason': reason, 'minimum_necessary': True}
        )
    
    def log_verification_attempt(
        self,
        session_id: str,
        verification_type: str,
        success: bool,
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log identity verification attempt"""
        return self.log_event(
            event_type='AUTH',
            user_id=details.get('user_id') if details else None,
            session_id=session_id,
            action=f'VERIFY_{verification_type}',
            success=success,
            details=details
        )
    
    def log_consent_capture(
        self,
        user_id: str,
        session_id: str,
        consent_type: str,
        consent_given: bool
    ) -> str:
        """Log consent capture (HIPAA required)"""
        return self.log_event(
            event_type='CONSENT',
            user_id=user_id,
            session_id=session_id,
            action='CAPTURE_CONSENT',
            success=True,
            details={
                'consent_type': consent_type,
                'consent_given': consent_given,
                'consent_timestamp': datetime.datetime.utcnow().isoformat() + 'Z'
            }
        )
    
    def log_session_event(
        self,
        session_id: str,
        event: str,
        user_id: Optional[str] = None
    ) -> str:
        """Log session lifecycle event"""
        return self.log_event(
            event_type='SESSION',
            user_id=user_id,
            session_id=session_id,
            action=event,
            success=True
        )
    
    def log_escalation(
        self,
        session_id: str,
        reason: str,
        keyword_detected: Optional[str] = None
    ) -> str:
        """Log conversation escalation"""
        return self.log_event(
            event_type='ESCALATION',
            user_id=None,
            session_id=session_id,
            action='ESCALATE_TO_STAFF',
            success=True,
            details={
                'reason': reason,
                'keyword_detected': keyword_detected
            }
        )
