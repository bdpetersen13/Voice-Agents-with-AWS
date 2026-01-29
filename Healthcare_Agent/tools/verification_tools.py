"""
Identity Verification Tools
HIPAA-compliant patient identity verification

Verification Levels:
- Level 1 (LIGHT): Name + DOB
- Level 2 (STANDARD): Level 1 + Phone/Email verification
- Level 3 (FULL): Level 2 + MRN/Patient ID

Rule: Scheduling = Level 1, Medical details = Escalate
"""
import datetime
from typing import Dict, Any
from tools.base_tool import BaseTool
from config.constants import (
    VERIFICATION_LEVEL_LIGHT,
    VERIFICATION_LEVEL_STANDARD,
    VERIFICATION_LEVEL_FULL
)


class VerifyIdentityTool(BaseTool):
    """Verify patient identity with Name + DOB (Level 1)"""
    
    def __init__(self, dynamodb, patients_table, session_manager, audit_logger):
        super().__init__(dynamodb)
        self.patients_table = patients_table
        self.session_manager = session_manager
        self.audit_logger = audit_logger
    
    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify identity using Name + Date of Birth
        
        Args:
            firstName: Patient's first name
            lastName: Patient's last name
            dateOfBirth: Date of birth (YYYY-MM-DD)
            sessionId: Session identifier
            
        Returns:
            verified: Boolean
            patientId: Patient ID if verified
            message: Status message
        """
        try:
            first_name = content_data.get("firstName")
            last_name = content_data.get("lastName")
            dob = content_data.get("dateOfBirth")
            session_id = content_data.get("sessionId")
            
            if not all([first_name, last_name, dob, session_id]):
                return {"error": "firstName, lastName, dateOfBirth, and sessionId are required."}
            
            # Log verification attempt
            self.audit_logger.log_verification_attempt(
                session_id=session_id,
                verification_type='NAME_DOB',
                success=False,
                details={'firstName': first_name, 'lastName': last_name}
            )
            
            # Search for patient by name and DOB
            # In production, this would use a secure index
            response = self.patients_table.scan(
                FilterExpression="firstName = :fn AND lastName = :ln AND dateOfBirth = :dob",
                ExpressionAttributeValues={
                    ':fn': first_name,
                    ':ln': last_name,
                    ':dob': dob
                }
            )
            
            items = response.get('Items', [])
            
            if not items:
                # Log failed attempt
                self.audit_logger.log_verification_attempt(
                    session_id=session_id,
                    verification_type='NAME_DOB',
                    success=False,
                    details={'reason': 'not_found'}
                )
                return {
                    "verified": False,
                    "message": "We couldn't find a patient with that name and date of birth. Please verify the information or call us to register."
                }
            
            if len(items) > 1:
                # Multiple matches - need additional verification
                return {
                    "verified": False,
                    "needsAdditionalVerification": True,
                    "message": "We found multiple patients with that name. For security, please provide your phone number or email for additional verification."
                }
            
            patient = items[0]
            patient_id = patient['patientId']
            
            # Mark session as verified (Level 1)
            self.session_manager.set_verified(
                session_id=session_id,
                user_id=patient_id,
                verification_level=VERIFICATION_LEVEL_LIGHT
            )
            
            # Log successful verification
            self.audit_logger.log_verification_attempt(
                session_id=session_id,
                verification_type='NAME_DOB',
                success=True,
                details={'user_id': patient_id}
            )
            
            # Log PHI access (reading patient data)
            self.audit_logger.log_phi_access(
                user_id=patient_id,
                session_id=session_id,
                resource_type='PATIENT',
                resource_id=patient_id,
                action='READ',
                reason='Identity verification for appointment scheduling'
            )
            
            return {
                "verified": True,
                "patientId": patient_id,
                "verificationLevel": VERIFICATION_LEVEL_LIGHT,
                "firstName": patient.get('firstName'),
                "message": f"Welcome back, {patient.get('firstName')}! Your identity has been verified."
            }
            
        except Exception as e:
            self.audit_logger.log_verification_attempt(
                session_id=content_data.get("sessionId", "unknown"),
                verification_type='NAME_DOB',
                success=False,
                details={'error': str(e)}
            )
            return {"error": str(e)}


class VerifyPhoneTool(BaseTool):
    """Verify phone number for Level 2 verification"""
    
    def __init__(self, dynamodb, patients_table, session_manager, audit_logger):
        super().__init__(dynamodb)
        self.patients_table = patients_table
        self.session_manager = session_manager
        self.audit_logger = audit_logger
    
    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify phone number matches patient record
        
        Args:
            patientId: Patient ID (from Level 1 verification)
            phoneNumber: Phone number to verify
            sessionId: Session identifier
            
        Returns:
            verified: Boolean
            verificationLevel: New verification level
        """
        try:
            patient_id = content_data.get("patientId")
            phone_number = content_data.get("phoneNumber")
            session_id = content_data.get("sessionId")
            
            if not all([patient_id, phone_number, session_id]):
                return {"error": "patientId, phoneNumber, and sessionId are required."}
            
            # Get patient record
            response = self.patients_table.get_item(Key={'patientId': patient_id})
            
            if 'Item' not in response:
                return {"error": "Patient not found."}
            
            patient = response['Item']
            stored_phone = patient.get('phoneNumber', '').replace('-', '').replace('(', '').replace(')', '').replace(' ', '')
            input_phone = phone_number.replace('-', '').replace('(', '').replace(')', '').replace(' ', '')
            
            if stored_phone != input_phone:
                self.audit_logger.log_verification_attempt(
                    session_id=session_id,
                    verification_type='PHONE',
                    success=False,
                    details={'user_id': patient_id, 'reason': 'phone_mismatch'}
                )
                return {
                    "verified": False,
                    "message": "The phone number doesn't match our records. Please try again or contact us."
                }
            
            # Upgrade to Level 2 verification
            self.session_manager.set_verified(
                session_id=session_id,
                user_id=patient_id,
                verification_level=VERIFICATION_LEVEL_STANDARD
            )
            
            self.audit_logger.log_verification_attempt(
                session_id=session_id,
                verification_type='PHONE',
                success=True,
                details={'user_id': patient_id}
            )
            
            return {
                "verified": True,
                "verificationLevel": VERIFICATION_LEVEL_STANDARD,
                "message": "Phone number verified successfully."
            }
            
        except Exception as e:
            return {"error": str(e)}


class VerifyEmailTool(BaseTool):
    """Verify email for Level 2 verification"""
    
    def __init__(self, dynamodb, patients_table, session_manager, audit_logger):
        super().__init__(dynamodb)
        self.patients_table = patients_table
        self.session_manager = session_manager
        self.audit_logger = audit_logger
    
    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify email matches patient record"""
        try:
            patient_id = content_data.get("patientId")
            email = content_data.get("email")
            session_id = content_data.get("sessionId")
            
            if not all([patient_id, email, session_id]):
                return {"error": "patientId, email, and sessionId are required."}
            
            response = self.patients_table.get_item(Key={'patientId': patient_id})
            
            if 'Item' not in response:
                return {"error": "Patient not found."}
            
            patient = response['Item']
            
            if patient.get('email', '').lower() != email.lower():
                self.audit_logger.log_verification_attempt(
                    session_id=session_id,
                    verification_type='EMAIL',
                    success=False,
                    details={'user_id': patient_id, 'reason': 'email_mismatch'}
                )
                return {
                    "verified": False,
                    "message": "The email doesn't match our records."
                }
            
            # Upgrade to Level 2
            self.session_manager.set_verified(
                session_id=session_id,
                user_id=patient_id,
                verification_level=VERIFICATION_LEVEL_STANDARD
            )
            
            self.audit_logger.log_verification_attempt(
                session_id=session_id,
                verification_type='EMAIL',
                success=True,
                details={'user_id': patient_id}
            )
            
            return {
                "verified": True,
                "verificationLevel": VERIFICATION_LEVEL_STANDARD,
                "message": "Email verified successfully."
            }
            
        except Exception as e:
            return {"error": str(e)}


class SetupProxyTool(BaseTool):
    """Setup proxy access (parent, caregiver, legal guardian)"""
    
    def __init__(self, dynamodb, patients_table, session_manager, audit_logger):
        super().__init__(dynamodb)
        self.patients_table = patients_table
        self.session_manager = session_manager
        self.audit_logger = audit_logger
    
    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify proxy relationship
        
        Args:
            proxyName: Name of person calling
            relationship: Relationship to patient (parent, spouse, guardian, caregiver)
            patientFirstName: Patient's first name
            patientLastName: Patient's last name
            patientDOB: Patient's date of birth
            sessionId: Session identifier
            
        Returns:
            verified: Boolean
            proxyType: Type of proxy
            patientId: Patient ID if verified
        """
        try:
            proxy_name = content_data.get("proxyName")
            relationship = content_data.get("relationship")
            patient_first = content_data.get("patientFirstName")
            patient_last = content_data.get("patientLastName")
            patient_dob = content_data.get("patientDOB")
            session_id = content_data.get("sessionId")
            
            if not all([proxy_name, relationship, patient_first, patient_last, patient_dob, session_id]):
                return {"error": "All proxy and patient information is required."}
            
            # Find patient
            response = self.patients_table.scan(
                FilterExpression="firstName = :fn AND lastName = :ln AND dateOfBirth = :dob",
                ExpressionAttributeValues={
                    ':fn': patient_first,
                    ':ln': patient_last,
                    ':dob': patient_dob
                }
            )
            
            items = response.get('Items', [])
            
            if not items:
                return {
                    "verified": False,
                    "message": "Patient not found with provided information."
                }
            
            patient = items[0]
            patient_id = patient['patientId']
            
            # Check if proxy is authorized (in production, verify against authorized proxy list)
            authorized_proxies = patient.get('authorizedProxies', [])
            
            # For minors (<18), parent/guardian is automatically authorized
            dob = datetime.datetime.strptime(patient_dob, '%Y-%m-%d')
            age = (datetime.datetime.now() - dob).days // 365
            
            is_minor = age < 18
            is_authorized = any(
                proxy.get('name') == proxy_name and proxy.get('relationship') == relationship
                for proxy in authorized_proxies
            )
            
            if not (is_minor and relationship in ['parent', 'guardian']) and not is_authorized:
                self.audit_logger.log_verification_attempt(
                    session_id=session_id,
                    verification_type='PROXY',
                    success=False,
                    details={'reason': 'unauthorized_proxy', 'patient_id': patient_id}
                )
                return {
                    "verified": False,
                    "message": "You are not authorized as a proxy for this patient. Please contact the office to set up proxy access."
                }
            
            # Set session as proxy-verified
            self.session_manager.set_verified(
                session_id=session_id,
                user_id=f"{patient_id}_PROXY_{proxy_name}",
                verification_level=VERIFICATION_LEVEL_LIGHT
            )
            
            self.audit_logger.log_verification_attempt(
                session_id=session_id,
                verification_type='PROXY',
                success=True,
                details={'user_id': patient_id, 'proxy_name': proxy_name, 'relationship': relationship}
            )
            
            self.audit_logger.log_phi_access(
                user_id=f"{patient_id}_PROXY_{proxy_name}",
                session_id=session_id,
                resource_type='PATIENT',
                resource_id=patient_id,
                action='READ',
                reason=f'Proxy access by {relationship} for appointment scheduling'
            )
            
            return {
                "verified": True,
                "proxyType": relationship,
                "patientId": patient_id,
                "patientName": f"{patient_first} {patient_last}",
                "message": f"Proxy access verified. You can manage appointments for {patient_first} {patient_last}."
            }
            
        except Exception as e:
            return {"error": str(e)}


class CaptureConsentTool(BaseTool):
    """Capture explicit consent (HIPAA required)"""
    
    def __init__(self, dynamodb, session_manager, audit_logger):
        super().__init__(dynamodb)
        self.session_manager = session_manager
        self.audit_logger = audit_logger
    
    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Capture explicit consent for voice interaction
        
        Args:
            sessionId: Session identifier
            patientId: Patient ID
            consentGiven: Boolean consent
            consentType: Type of consent (VOICE_INTERACTION, PHI_DISCLOSURE, etc.)
            
        Returns:
            consentCaptured: Boolean
            consentId: Consent record ID
        """
        try:
            session_id = content_data.get("sessionId")
            patient_id = content_data.get("patientId")
            consent_given = content_data.get("consentGiven", False)
            consent_type = content_data.get("consentType", "VOICE_INTERACTION")
            
            if not all([session_id, patient_id]):
                return {"error": "sessionId and patientId are required."}
            
            # Update session
            self.session_manager.set_consent(session_id, consent_given)
            
            # Log consent capture (HIPAA required)
            consent_id = self.audit_logger.log_consent_capture(
                user_id=patient_id,
                session_id=session_id,
                consent_type=consent_type,
                consent_given=consent_given
            )
            
            if not consent_given:
                return {
                    "consentCaptured": True,
                    "consentId": consent_id,
                    "consentGiven": False,
                    "message": "Consent declined. Ending session. Please call us directly to schedule an appointment."
                }
            
            return {
                "consentCaptured": True,
                "consentId": consent_id,
                "consentGiven": True,
                "message": "Thank you for providing consent. I can now assist you with scheduling."
            }
            
        except Exception as e:
            return {"error": str(e)}
