"""
Insurance and Referral Verification Tools
Check insurance coverage and referral requirements
"""
from typing import Dict, Any
from tools.base_tool import BaseTool
from config.constants import INSURANCE_VERIFIED, REFERRAL_REQUIRED, REFERRAL_RECEIVED


class CheckInsuranceTool(BaseTool):
    """Verify insurance coverage"""
    
    def __init__(self, dynamodb, insurance_table, patients_table, 
                 session_manager, audit_logger):
        super().__init__(dynamodb)
        self.insurance_table = insurance_table
        self.patients_table = patients_table
        self.session_manager = session_manager
        self.audit_logger = audit_logger
    
    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check insurance coverage for appointment
        
        Args:
            patientId: Patient ID
            providerId: Provider ID
            appointmentType: Type of appointment
            sessionId: Session identifier
            
        Returns:
            coverageStatus: Coverage status
            copay: Copay amount (if applicable)
            requiresPreAuth: Boolean
        """
        try:
            patient_id = content_data.get("patientId")
            provider_id = content_data.get("providerId")
            appt_type = content_data.get("appointmentType")
            session_id = content_data.get("sessionId")
            
            if not all([patient_id, session_id]):
                return {"error": "patientId and sessionId are required."}
            
            # Verify session
            if self.session_manager.requires_verification(session_id, required_level=1):
                return {"error": "Identity verification required."}
            
            # Get patient insurance
            patient = self.patients_table.get_item(Key={'patientId': patient_id}).get('Item', {})
            
            insurance_id = patient.get('insuranceId')
            
            if not insurance_id:
                return {
                    "coverageStatus": "NO_INSURANCE",
                    "message": "No insurance on file. Appointment will be self-pay."
                }
            
            # Check insurance coverage
            insurance = self.insurance_table.get_item(Key={'insuranceId': insurance_id}).get('Item', {})
            
            # Audit log (accessing insurance info is PHI)
            self.audit_logger.log_phi_access(
                user_id=patient_id,
                session_id=session_id,
                resource_type='INSURANCE',
                resource_id=insurance_id,
                action='READ',
                reason='Verifying insurance coverage for appointment'
            )
            
            coverage_status = insurance.get('status', INSURANCE_VERIFIED)
            copay = insurance.get('copay', '0.00')
            requires_pre_auth = appt_type in insurance.get('requiresPreAuth', [])
            
            return {
                "coverageStatus": coverage_status,
                "insuranceProvider": insurance.get('provider'),
                "memberId": insurance.get('memberId'),
                "copay": str(copay),
                "requiresPreAuth": requires_pre_auth,
                "message": f"Insurance verified. Copay: ${copay}" + 
                          (" (Pre-authorization required)" if requires_pre_auth else "")
            }
            
        except Exception as e:
            return {"error": str(e)}


class CheckReferralTool(BaseTool):
    """Check referral requirements"""
    
    def __init__(self, dynamodb, referrals_table, patients_table,
                 session_manager, audit_logger):
        super().__init__(dynamodb)
        self.referrals_table = referrals_table
        self.patients_table = patients_table
        self.session_manager = session_manager
        self.audit_logger = audit_logger
    
    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if referral is required and on file
        
        Args:
            patientId: Patient ID
            specialty: Specialty being scheduled
            sessionId: Session identifier
            
        Returns:
            referralStatus: Status of referral
            referralRequired: Boolean
            referralOnFile: Boolean
        """
        try:
            patient_id = content_data.get("patientId")
            specialty = content_data.get("specialty")
            session_id = content_data.get("sessionId")
            
            if not all([patient_id, specialty, session_id]):
                return {"error": "patientId, specialty, and sessionId are required."}
            
            # Verify session
            if self.session_manager.requires_verification(session_id, required_level=1):
                return {"error": "Identity verification required."}
            
            # Get patient insurance to check if referral required
            patient = self.patients_table.get_item(Key={'patientId': patient_id}).get('Item', {})
            
            # Check if specialty requires referral
            specialties_requiring_referral = [
                "cardiology", "neurology", "orthopedics", "rheumatology",
                "endocrinology", "gastroenterology", "pulmonology"
            ]
            
            referral_required = specialty.lower() in specialties_requiring_referral
            
            if not referral_required:
                return {
                    "referralRequired": False,
                    "referralStatus": "NOT_REQUIRED",
                    "message": "No referral required for this specialty."
                }
            
            # Check for active referral
            response = self.referrals_table.scan(
                FilterExpression="patientId = :pid AND specialty = :spec AND #status = :active",
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':pid': patient_id,
                    ':spec': specialty,
                    ':active': REFERRAL_RECEIVED
                }
            )
            
            referrals = response.get('Items', [])
            
            # Audit log
            self.audit_logger.log_phi_access(
                user_id=patient_id,
                session_id=session_id,
                resource_type='REFERRAL',
                resource_id='SEARCH',
                action='READ',
                reason='Checking referral status for appointment'
            )
            
            if referrals:
                referral = referrals[0]
                return {
                    "referralRequired": True,
                    "referralOnFile": True,
                    "referralStatus": REFERRAL_RECEIVED,
                    "referralId": referral.get('referralId'),
                    "referringProvider": referral.get('referringProvider'),
                    "message": "Referral on file and valid."
                }
            else:
                return {
                    "referralRequired": True,
                    "referralOnFile": False,
                    "referralStatus": REFERRAL_REQUIRED,
                    "message": "Referral required but not on file. Please obtain a referral from your primary care provider first."
                }
            
        except Exception as e:
            return {"error": str(e)}
