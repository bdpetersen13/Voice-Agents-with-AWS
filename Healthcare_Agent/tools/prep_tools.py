"""
Prep and Instruction Tools
Send appointment preparation instructions
"""
import datetime
from typing import Dict, Any
from tools.base_tool import BaseTool


class SendPrepInstructionsTool(BaseTool):
    """Send pre-appointment preparation instructions"""
    
    def __init__(self, dynamodb, appointments_table, patients_table, audit_logger):
        super().__init__(dynamodb)
        self.appointments_table = appointments_table
        self.patients_table = patients_table
        self.audit_logger = audit_logger
    
    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send preparation instructions for appointment
        
        Args:
            appointmentId: Appointment ID
            patientId: Patient ID
            sessionId: Session identifier
            
        Returns:
            instructionsSent: Boolean
            instructions: List of instructions
            message: Confirmation
        """
        try:
            appt_id = content_data.get("appointmentId")
            patient_id = content_data.get("patientId")
            session_id = content_data.get("sessionId")
            
            if not all([appt_id, patient_id, session_id]):
                return {"error": "appointmentId, patientId, and sessionId are required."}
            
            # Get appointment
            appt = self.appointments_table.get_item(Key={'appointmentId': appt_id}).get('Item', {})
            
            # Get patient contact
            patient = self.patients_table.get_item(Key={'patientId': patient_id}).get('Item', {})
            
            # Determine instructions based on appointment type
            appt_type = appt.get('appointmentType', '')
            instructions = self._get_instructions(appt_type, appt)
            
            # Update appointment with instructions sent
            self.appointments_table.update_item(
                Key={'appointmentId': appt_id},
                UpdateExpression="SET prepInstructionsSent = :sent, prepInstructionsSentAt = :now",
                ExpressionAttributeValues={
                    ':sent': True,
                    ':now': datetime.datetime.utcnow().isoformat() + 'Z'
                }
            )
            
            # Audit log
            self.audit_logger.log_event(
                event_type='APPOINTMENT',
                user_id=patient_id,
                session_id=session_id,
                action='SEND_PREP_INSTRUCTIONS',
                resource_type='APPOINTMENT',
                resource_id=appt_id,
                success=True,
                phi_accessed=True,
                details={'appointment_type': appt_type}
            )
            
            return {
                "instructionsSent": True,
                "instructions": instructions,
                "appointmentDate": appt.get('date'),
                "appointmentTime": appt.get('startTime'),
                "arrivalTime": self._calculate_arrival_time(appt.get('startTime')),
                "message": "Preparation instructions sent. Please follow these guidelines before your appointment."
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _get_instructions(self, appt_type: str, appt: Dict[str, Any]) -> Dict[str, Any]:
        """Generate instructions based on appointment type"""
        base_instructions = {
            "what_to_bring": [
                "Photo ID",
                "Insurance card",
                "List of current medications",
                "Payment method for copay"
            ],
            "arrival": "Please arrive 15 minutes before your scheduled time for check-in.",
            "parking": "Free parking is available in the main lot."
        }
        
        # Add type-specific instructions
        if appt_type in ["procedure", "surgery"]:
            base_instructions["fasting"] = "Do not eat or drink anything after midnight the night before."
            base_instructions["medications"] = "Take your regular medications with a small sip of water unless instructed otherwise."
            base_instructions["transportation"] = "Arrange for someone to drive you home after the procedure."
        
        elif appt_type == "screening":
            base_instructions["prep"] = "Follow the preparation instructions provided by your doctor."
        
        elif appt_type == "new_patient":
            base_instructions["forms"] = "Complete all new patient forms online before your visit to save time."
        
        return base_instructions
    
    def _calculate_arrival_time(self, appt_time: str) -> str:
        """Calculate recommended arrival time (15 minutes early)"""
        try:
            time_obj = datetime.datetime.strptime(appt_time, '%H:%M')
            arrival = time_obj - datetime.timedelta(minutes=15)
            return arrival.strftime('%H:%M')
        except:
            return appt_time
