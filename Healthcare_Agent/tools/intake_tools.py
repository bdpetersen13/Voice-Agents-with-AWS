"""
Patient Intake Tools
Handle new patient intake and reason for visit collection
"""
import datetime
from typing import Dict, Any
from tools.base_tool import BaseTool


class StartIntakeTool(BaseTool):
    """Start patient intake process"""
    
    def __init__(self, dynamodb, patients_table, intake_forms_table,
                 session_manager, audit_logger):
        super().__init__(dynamodb)
        self.patients_table = patients_table
        self.intake_forms_table = intake_forms_table
        self.session_manager = session_manager
        self.audit_logger = audit_logger
    
    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine if new or existing patient and start intake
        
        Args:
            patientId: Optional patient ID (if existing)
            firstName: First name
            lastName: Last name
            dateOfBirth: DOB
            sessionId: Session identifier
            
        Returns:
            intakeType: "new_patient" or "existing_patient"
            requiredForms: List of required forms
            intakeId: Intake record ID
        """
        try:
            patient_id = content_data.get("patientId")
            first_name = content_data.get("firstName")
            last_name = content_data.get("lastName")
            dob = content_data.get("dateOfBirth")
            session_id = content_data.get("sessionId")
            
            if not all([first_name, last_name, dob, session_id]):
                return {"error": "firstName, lastName, dateOfBirth, and sessionId are required."}
            
            # Check if existing patient
            if patient_id:
                patient = self.patients_table.get_item(Key={'patientId': patient_id}).get('Item')
                if patient:
                    intake_type = "existing_patient"
                    required_forms = ["consent_form", "insurance_form"]
                else:
                    intake_type = "new_patient"
                    required_forms = ["new_patient_form", "medical_history", "consent_form", "insurance_form"]
            else:
                intake_type = "new_patient"
                required_forms = ["new_patient_form", "medical_history", "consent_form", "insurance_form"]
            
            # Create intake record
            intake_id = f"INTAKE-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            intake_record = {
                'intakeId': intake_id,
                'patientId': patient_id,
                'firstName': first_name,
                'lastName': last_name,
                'dateOfBirth': dob,
                'intakeType': intake_type,
                'requiredForms': required_forms,
                'createdAt': datetime.datetime.utcnow().isoformat() + 'Z',
                'status': 'IN_PROGRESS',
                'sessionId': session_id
            }
            
            self.intake_forms_table.put_item(Item=intake_record)
            
            # Audit log
            self.audit_logger.log_event(
                event_type='INTAKE',
                user_id=patient_id,
                session_id=session_id,
                action='START_INTAKE',
                resource_type='INTAKE',
                resource_id=intake_id,
                success=True,
                phi_accessed=bool(patient_id),
                details={'intake_type': intake_type}
            )
            
            return {
                "success": True,
                "intakeType": intake_type,
                "requiredForms": required_forms,
                "intakeId": intake_id,
                "message": f"{'New patient' if intake_type == 'new_patient' else 'Existing patient'} intake started. {len(required_forms)} form(s) required."
            }
            
        except Exception as e:
            return {"error": str(e)}


class CollectReasonTool(BaseTool):
    """Collect structured reason for visit"""
    
    def __init__(self, dynamodb, intake_forms_table, audit_logger):
        super().__init__(dynamodb)
        self.intake_forms_table = intake_forms_table
        self.audit_logger = audit_logger
    
    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Collect reason for visit using controlled vocabulary
        
        Args:
            intakeId: Intake record ID
            reasonCategory: Category (annual_checkup, follow_up, new_concern, procedure, screening)
            specificReason: Optional brief description (NO medical details)
            sessionId: Session identifier
            
        Returns:
            reasonCaptured: Boolean
            message: Confirmation
        """
        try:
            intake_id = content_data.get("intakeId")
            reason_category = content_data.get("reasonCategory")
            specific_reason = content_data.get("specificReason", "")
            session_id = content_data.get("sessionId")
            
            if not all([intake_id, reason_category, session_id]):
                return {"error": "intakeId, reasonCategory, and sessionId are required."}
            
            # Valid categories (controlled vocabulary - no medical details)
            valid_categories = [
                "annual_checkup", "follow_up", "new_concern", "procedure",
                "screening", "wellness_visit", "preventive_care"
            ]
            
            if reason_category not in valid_categories:
                return {
                    "error": f"Invalid reason category. Must be one of: {', '.join(valid_categories)}"
                }
            
            # Update intake record
            self.intake_forms_table.update_item(
                Key={'intakeId': intake_id},
                UpdateExpression="SET reasonCategory = :cat, specificReason = :spec",
                ExpressionAttributeValues={
                    ':cat': reason_category,
                    ':spec': specific_reason
                }
            )
            
            # Audit log
            self.audit_logger.log_event(
                event_type='INTAKE',
                user_id=None,
                session_id=session_id,
                action='COLLECT_REASON',
                resource_type='INTAKE',
                resource_id=intake_id,
                success=True,
                phi_accessed=False,
                details={'reason_category': reason_category}
            )
            
            return {
                "reasonCaptured": True,
                "reasonCategory": reason_category,
                "message": "Reason for visit recorded. This will help us prepare for your appointment."
            }
            
        except Exception as e:
            return {"error": str(e)}


class SendFormsTool(BaseTool):
    """Send intake forms to patient"""
    
    def __init__(self, dynamodb, intake_forms_table, patients_table, audit_logger):
        super().__init__(dynamodb)
        self.intake_forms_table = intake_forms_table
        self.patients_table = patients_table
        self.audit_logger = audit_logger
    
    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate and send intake form links
        
        Args:
            intakeId: Intake record ID
            patientId: Patient ID
            deliveryMethod: "email" or "sms"
            sessionId: Session identifier
            
        Returns:
            formsSent: Boolean
            formsLink: Secure link to forms
            message: Confirmation
        """
        try:
            intake_id = content_data.get("intakeId")
            patient_id = content_data.get("patientId")
            delivery_method = content_data.get("deliveryMethod", "email")
            session_id = content_data.get("sessionId")
            
            if not all([intake_id, patient_id, session_id]):
                return {"error": "intakeId, patientId, and sessionId are required."}
            
            # Get intake record
            intake = self.intake_forms_table.get_item(Key={'intakeId': intake_id}).get('Item', {})
            
            # Get patient contact info
            patient = self.patients_table.get_item(Key={'patientId': patient_id}).get('Item', {})
            
            # Generate secure form link (in production, this would be a real secure portal)
            forms_link = f"https://portal.healthcare.example.com/intake/{intake_id}"
            
            # Update intake with sent status
            self.intake_forms_table.update_item(
                Key={'intakeId': intake_id},
                UpdateExpression="SET formsSent = :sent, formsSentAt = :now, formsLink = :link, deliveryMethod = :method",
                ExpressionAttributeValues={
                    ':sent': True,
                    ':now': datetime.datetime.utcnow().isoformat() + 'Z',
                    ':link': forms_link,
                    ':method': delivery_method
                }
            )
            
            # Audit log
            self.audit_logger.log_event(
                event_type='INTAKE',
                user_id=patient_id,
                session_id=session_id,
                action='SEND_FORMS',
                resource_type='INTAKE',
                resource_id=intake_id,
                success=True,
                phi_accessed=True,
                details={'delivery_method': delivery_method}
            )
            
            contact = patient.get('email') if delivery_method == 'email' else patient.get('phoneNumber')
            
            return {
                "formsSent": True,
                "formsLink": forms_link,
                "requiredForms": intake.get('requiredForms', []),
                "deliveredTo": contact,
                "message": f"Intake forms sent to your {delivery_method}. Please complete them before your appointment."
            }
            
        except Exception as e:
            return {"error": str(e)}
