"""
Appointment Management Tools
HIPAA-compliant appointment scheduling, rescheduling, and cancellation

These tools handle the core appointment lifecycle with proper PHI protection
and audit logging.
"""
import datetime
import uuid
from typing import Dict, Any, List, Optional
from tools.base_tool import BaseTool
from config.constants import (
    SLOT_AVAILABLE, SLOT_HELD, SLOT_BOOKED,
    APPT_STATUS_SCHEDULED, APPT_STATUS_CONFIRMED, APPT_STATUS_CANCELLED,
    SLOT_HOLD_MINUTES
)


class SearchAvailabilityTool(BaseTool):
    """Search for available appointment slots"""
    
    def __init__(self, dynamodb, availability_table, providers_table, locations_table, audit_logger):
        super().__init__(dynamodb)
        self.availability_table = availability_table
        self.providers_table = providers_table
        self.locations_table = locations_table
        self.audit_logger = audit_logger
    
    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search for available appointment slots
        
        Args:
            providerId: Optional provider ID
            locationId: Optional location ID
            specialty: Optional specialty filter
            startDate: Start date for search (YYYY-MM-DD)
            endDate: End date for search (YYYY-MM-DD)
            timePreference: Optional ("morning", "afternoon", "evening", "after_3pm")
            appointmentType: Type of appointment
            sessionId: Session identifier
            
        Returns:
            availableSlots: List of available time slots
            count: Number of slots found
        """
        try:
            provider_id = content_data.get("providerId")
            location_id = content_data.get("locationId")
            specialty = content_data.get("specialty")
            start_date = content_data.get("startDate")
            end_date = content_data.get("endDate")
            time_pref = content_data.get("timePreference")
            appt_type = content_data.get("appointmentType")
            session_id = content_data.get("sessionId")
            
            if not start_date:
                return {"error": "startDate is required for availability search."}
            
            # Default to 2 weeks if no end date
            if not end_date:
                start = datetime.datetime.strptime(start_date, '%Y-%m-%d')
                end = start + datetime.timedelta(days=14)
                end_date = end.strftime('%Y-%m-%d')
            
            # Build filter expression
            filter_parts = ["#date BETWEEN :start AND :end", "#status = :available"]
            expr_values = {
                ':start': start_date,
                ':end': end_date,
                ':available': SLOT_AVAILABLE
            }
            expr_names = {'#date': 'date', '#status': 'status'}
            
            if provider_id:
                filter_parts.append("providerId = :pid")
                expr_values[':pid'] = provider_id
            
            if location_id:
                filter_parts.append("locationId = :lid")
                expr_values[':lid'] = location_id
            
            filter_expression = " AND ".join(filter_parts)
            
            # Search availability
            response = self.availability_table.scan(
                FilterExpression=filter_expression,
                ExpressionAttributeNames=expr_names,
                ExpressionAttributeValues=expr_values
            )
            
            slots = response.get('Items', [])
            
            # Apply time preference filter
            if time_pref:
                slots = self._filter_by_time_preference(slots, time_pref)
            
            # Sort by date and time
            slots.sort(key=lambda x: (x.get('date', ''), x.get('startTime', '')))
            
            # Convert decimals
            slots = [self.convert_decimals(slot) for slot in slots]
            
            # Limit to 20 results
            slots = slots[:20]
            
            # Enrich with provider/location details
            enriched_slots = []
            for slot in slots:
                enriched = slot.copy()
                
                # Get provider name
                if slot.get('providerId'):
                    provider = self.providers_table.get_item(
                        Key={'providerId': slot['providerId']}
                    ).get('Item', {})
                    enriched['providerName'] = provider.get('name')
                    enriched['specialty'] = provider.get('specialty')
                
                # Get location name
                if slot.get('locationId'):
                    location = self.locations_table.get_item(
                        Key={'locationId': slot['locationId']}
                    ).get('Item', {})
                    enriched['locationName'] = location.get('name')
                    enriched['address'] = location.get('address')
                
                enriched_slots.append(enriched)
            
            # Audit log (no PHI accessed for availability search)
            self.audit_logger.log_event(
                event_type='APPOINTMENT',
                user_id=None,
                session_id=session_id,
                action='SEARCH_AVAILABILITY',
                success=True,
                phi_accessed=False,
                details={
                    'start_date': start_date,
                    'end_date': end_date,
                    'results_count': len(enriched_slots)
                }
            )
            
            return {
                "success": True,
                "availableSlots": enriched_slots,
                "count": len(enriched_slots),
                "message": f"Found {len(enriched_slots)} available appointment slots."
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _filter_by_time_preference(self, slots: List[Dict], preference: str) -> List[Dict]:
        """Filter slots by time preference"""
        if preference == "morning":
            return [s for s in slots if s.get('startTime', '00:00') < '12:00']
        elif preference == "afternoon":
            return [s for s in slots if '12:00' <= s.get('startTime', '00:00') < '17:00']
        elif preference == "evening":
            return [s for s in slots if s.get('startTime', '00:00') >= '17:00']
        elif preference == "after_3pm":
            return [s for s in slots if s.get('startTime', '00:00') >= '15:00']
        return slots


class HoldSlotTool(BaseTool):
    """Hold an appointment slot temporarily during booking"""
    
    def __init__(self, dynamodb, availability_table, audit_logger):
        super().__init__(dynamodb)
        self.availability_table = availability_table
        self.audit_logger = audit_logger
    
    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hold a slot for 10 minutes to prevent double-booking
        
        Args:
            slotId: Availability slot ID
            sessionId: Session identifier
            
        Returns:
            held: Boolean
            expiresAt: When hold expires
            slotDetails: Slot information
        """
        try:
            slot_id = content_data.get("slotId")
            session_id = content_data.get("sessionId")
            
            if not all([slot_id, session_id]):
                return {"error": "slotId and sessionId are required."}
            
            # Get slot
            response = self.availability_table.get_item(Key={'slotId': slot_id})
            
            if 'Item' not in response:
                return {"error": "Slot not found."}
            
            slot = response['Item']
            
            if slot.get('status') != SLOT_AVAILABLE:
                return {
                    "held": False,
                    "message": "This slot is no longer available. Please search for another time."
                }
            
            # Hold slot
            hold_expires = datetime.datetime.utcnow() + datetime.timedelta(minutes=SLOT_HOLD_MINUTES)
            
            self.availability_table.update_item(
                Key={'slotId': slot_id},
                UpdateExpression="SET #status = :held, heldBy = :session, holdExpiresAt = :expires",
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':held': SLOT_HELD,
                    ':session': session_id,
                    ':expires': hold_expires.isoformat() + 'Z'
                }
            )
            
            # Audit log
            self.audit_logger.log_event(
                event_type='APPOINTMENT',
                user_id=None,
                session_id=session_id,
                action='HOLD_SLOT',
                resource_type='SLOT',
                resource_id=slot_id,
                success=True,
                phi_accessed=False,
                details={'hold_duration_minutes': SLOT_HOLD_MINUTES}
            )
            
            return {
                "held": True,
                "slotId": slot_id,
                "expiresAt": hold_expires.isoformat() + 'Z',
                "slotDetails": self.convert_decimals(slot),
                "message": f"Slot held for {SLOT_HOLD_MINUTES} minutes. Please confirm to book."
            }
            
        except Exception as e:
            return {"error": str(e)}


class ScheduleAppointmentTool(BaseTool):
    """Schedule a new appointment"""
    
    def __init__(self, dynamodb, appointments_table, availability_table, 
                 patients_table, session_manager, audit_logger):
        super().__init__(dynamodb)
        self.appointments_table = appointments_table
        self.availability_table = availability_table
        self.patients_table = patients_table
        self.session_manager = session_manager
        self.audit_logger = audit_logger
    
    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Schedule an appointment
        
        Args:
            patientId: Patient ID
            slotId: Held slot ID
            appointmentType: Type of appointment
            reasonForVisit: Structured reason (not medical details)
            sessionId: Session identifier
            
        Returns:
            scheduled: Boolean
            appointmentId: New appointment ID
            confirmationDetails: Appointment details
        """
        try:
            patient_id = content_data.get("patientId")
            slot_id = content_data.get("slotId")
            appt_type = content_data.get("appointmentType")
            reason = content_data.get("reasonForVisit", "General appointment")
            session_id = content_data.get("sessionId")
            
            if not all([patient_id, slot_id, session_id]):
                return {"error": "patientId, slotId, and sessionId are required."}
            
            # Verify session has minimum verification
            if self.session_manager.requires_verification(session_id, required_level=1):
                return {
                    "error": "Identity verification required before scheduling. Please verify your identity first."
                }
            
            # Get slot
            slot_response = self.availability_table.get_item(Key={'slotId': slot_id})
            
            if 'Item' not in slot_response:
                return {"error": "Slot not found."}
            
            slot = slot_response['Item']
            
            # Verify slot is held by this session or available
            if slot.get('status') == SLOT_HELD:
                if slot.get('heldBy') != session_id:
                    return {"error": "This slot is held by another session."}
            elif slot.get('status') != SLOT_AVAILABLE:
                return {"error": "This slot is no longer available."}
            
            # Create appointment
            appt_id = f"APPT-{datetime.datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
            
            appointment = {
                'appointmentId': appt_id,
                'patientId': patient_id,
                'providerId': slot.get('providerId'),
                'locationId': slot.get('locationId'),
                'date': slot.get('date'),
                'startTime': slot.get('startTime'),
                'endTime': slot.get('endTime'),
                'appointmentType': appt_type,
                'reasonForVisit': reason,
                'status': APPT_STATUS_SCHEDULED,
                'createdAt': datetime.datetime.utcnow().isoformat() + 'Z',
                'sessionId': session_id
            }
            
            # Save appointment
            self.appointments_table.put_item(Item=appointment)
            
            # Mark slot as booked
            self.availability_table.update_item(
                Key={'slotId': slot_id},
                UpdateExpression="SET #status = :booked, bookedBy = :appt",
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':booked': SLOT_BOOKED,
                    ':appt': appt_id
                }
            )
            
            # Audit log PHI access (accessing patient data for appointment)
            self.audit_logger.log_phi_access(
                user_id=patient_id,
                session_id=session_id,
                resource_type='APPOINTMENT',
                resource_id=appt_id,
                action='CREATE',
                reason='Scheduling new appointment'
            )
            
            return {
                "scheduled": True,
                "appointmentId": appt_id,
                "confirmationDetails": self.convert_decimals(appointment),
                "message": f"Appointment scheduled for {slot.get('date')} at {slot.get('startTime')}. Confirmation number: {appt_id}"
            }
            
        except Exception as e:
            return {"error": str(e)}


class RescheduleAppointmentTool(BaseTool):
    """Reschedule an existing appointment"""
    
    def __init__(self, dynamodb, appointments_table, availability_table, 
                 session_manager, audit_logger):
        super().__init__(dynamodb)
        self.appointments_table = appointments_table
        self.availability_table = availability_table
        self.session_manager = session_manager
        self.audit_logger = audit_logger
    
    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reschedule an appointment to a new time
        
        Args:
            appointmentId: Appointment to reschedule
            newSlotId: New slot ID
            sessionId: Session identifier
            patientId: Patient ID (for verification)
            
        Returns:
            rescheduled: Boolean
            newAppointmentDetails: Updated appointment info
        """
        try:
            appt_id = content_data.get("appointmentId")
            new_slot_id = content_data.get("newSlotId")
            session_id = content_data.get("sessionId")
            patient_id = content_data.get("patientId")
            
            if not all([appt_id, new_slot_id, session_id, patient_id]):
                return {"error": "appointmentId, newSlotId, sessionId, and patientId are required."}
            
            # Verify session
            if self.session_manager.requires_verification(session_id, required_level=1):
                return {"error": "Identity verification required."}
            
            # Get existing appointment
            appt_response = self.appointments_table.get_item(Key={'appointmentId': appt_id})
            
            if 'Item' not in appt_response:
                return {"error": "Appointment not found."}
            
            appt = appt_response['Item']
            
            # Verify patient owns this appointment
            if appt.get('patientId') != patient_id:
                return {"error": "This appointment does not belong to you."}
            
            # Get new slot
            new_slot_response = self.availability_table.get_item(Key={'slotId': new_slot_id})
            
            if 'Item' not in new_slot_response:
                return {"error": "New slot not found."}
            
            new_slot = new_slot_response['Item']
            
            if new_slot.get('status') not in [SLOT_AVAILABLE, SLOT_HELD]:
                return {"error": "New slot is not available."}
            
            # Release old slot (find by date/time/provider)
            old_slot_scan = self.availability_table.scan(
                FilterExpression="providerId = :pid AND #date = :d AND startTime = :st",
                ExpressionAttributeNames={'#date': 'date'},
                ExpressionAttributeValues={
                    ':pid': appt.get('providerId'),
                    ':d': appt.get('date'),
                    ':st': appt.get('startTime')
                }
            )
            
            if old_slot_scan.get('Items'):
                old_slot = old_slot_scan['Items'][0]
                self.availability_table.update_item(
                    Key={'slotId': old_slot['slotId']},
                    UpdateExpression="SET #status = :available REMOVE bookedBy",
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={':available': SLOT_AVAILABLE}
                )
            
            # Update appointment
            self.appointments_table.update_item(
                Key={'appointmentId': appt_id},
                UpdateExpression="SET #date = :d, startTime = :st, endTime = :et, providerId = :pid, locationId = :lid, rescheduledAt = :now",
                ExpressionAttributeNames={'#date': 'date'},
                ExpressionAttributeValues={
                    ':d': new_slot.get('date'),
                    ':st': new_slot.get('startTime'),
                    ':et': new_slot.get('endTime'),
                    ':pid': new_slot.get('providerId'),
                    ':lid': new_slot.get('locationId'),
                    ':now': datetime.datetime.utcnow().isoformat() + 'Z'
                }
            )
            
            # Book new slot
            self.availability_table.update_item(
                Key={'slotId': new_slot_id},
                UpdateExpression="SET #status = :booked, bookedBy = :appt",
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':booked': SLOT_BOOKED,
                    ':appt': appt_id
                }
            )
            
            # Audit log
            self.audit_logger.log_phi_access(
                user_id=patient_id,
                session_id=session_id,
                resource_type='APPOINTMENT',
                resource_id=appt_id,
                action='UPDATE',
                reason='Rescheduling appointment'
            )
            
            # Get updated appointment
            updated_appt = self.appointments_table.get_item(Key={'appointmentId': appt_id})['Item']
            
            return {
                "rescheduled": True,
                "appointmentId": appt_id,
                "newAppointmentDetails": self.convert_decimals(updated_appt),
                "message": f"Appointment rescheduled to {new_slot.get('date')} at {new_slot.get('startTime')}."
            }
            
        except Exception as e:
            return {"error": str(e)}


class CancelAppointmentTool(BaseTool):
    """Cancel an appointment"""
    
    def __init__(self, dynamodb, appointments_table, availability_table,
                 session_manager, audit_logger):
        super().__init__(dynamodb)
        self.appointments_table = appointments_table
        self.availability_table = availability_table
        self.session_manager = session_manager
        self.audit_logger = audit_logger
    
    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cancel an appointment and release the slot
        
        Args:
            appointmentId: Appointment to cancel
            patientId: Patient ID (for verification)
            sessionId: Session identifier
            cancellationReason: Optional reason
            
        Returns:
            cancelled: Boolean
            message: Confirmation message
        """
        try:
            appt_id = content_data.get("appointmentId")
            patient_id = content_data.get("patientId")
            session_id = content_data.get("sessionId")
            reason = content_data.get("cancellationReason", "Patient requested")
            
            if not all([appt_id, patient_id, session_id]):
                return {"error": "appointmentId, patientId, and sessionId are required."}
            
            # Verify session
            if self.session_manager.requires_verification(session_id, required_level=1):
                return {"error": "Identity verification required."}
            
            # Get appointment
            appt_response = self.appointments_table.get_item(Key={'appointmentId': appt_id})
            
            if 'Item' not in appt_response:
                return {"error": "Appointment not found."}
            
            appt = appt_response['Item']
            
            # Verify ownership
            if appt.get('patientId') != patient_id:
                return {"error": "This appointment does not belong to you."}
            
            # Update appointment status
            self.appointments_table.update_item(
                Key={'appointmentId': appt_id},
                UpdateExpression="SET #status = :cancelled, cancelledAt = :now, cancellationReason = :reason",
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':cancelled': APPT_STATUS_CANCELLED,
                    ':now': datetime.datetime.utcnow().isoformat() + 'Z',
                    ':reason': reason
                }
            )
            
            # Release slot
            slot_scan = self.availability_table.scan(
                FilterExpression="providerId = :pid AND #date = :d AND startTime = :st",
                ExpressionAttributeNames={'#date': 'date'},
                ExpressionAttributeValues={
                    ':pid': appt.get('providerId'),
                    ':d': appt.get('date'),
                    ':st': appt.get('startTime')
                }
            )
            
            if slot_scan.get('Items'):
                slot = slot_scan['Items'][0]
                self.availability_table.update_item(
                    Key={'slotId': slot['slotId']},
                    UpdateExpression="SET #status = :available REMOVE bookedBy",
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={':available': SLOT_AVAILABLE}
                )
            
            # Audit log
            self.audit_logger.log_phi_access(
                user_id=patient_id,
                session_id=session_id,
                resource_type='APPOINTMENT',
                resource_id=appt_id,
                action='CANCEL',
                reason='Patient-initiated cancellation'
            )
            
            return {
                "cancelled": True,
                "appointmentId": appt_id,
                "message": f"Appointment cancelled. The slot is now available for other patients."
            }
            
        except Exception as e:
            return {"error": str(e)}


class ConfirmAppointmentTool(BaseTool):
    """Confirm appointment details"""
    
    def __init__(self, dynamodb, appointments_table, session_manager, audit_logger):
        super().__init__(dynamodb)
        self.appointments_table = appointments_table
        self.session_manager = session_manager
        self.audit_logger = audit_logger
    
    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Confirm an appointment
        
        Args:
            appointmentId: Appointment ID
            patientId: Patient ID
            sessionId: Session identifier
            
        Returns:
            confirmed: Boolean
            appointmentDetails: Full appointment details
        """
        try:
            appt_id = content_data.get("appointmentId")
            patient_id = content_data.get("patientId")
            session_id = content_data.get("sessionId")
            
            if not all([appt_id, patient_id, session_id]):
                return {"error": "appointmentId, patientId, and sessionId are required."}
            
            # Get appointment
            response = self.appointments_table.get_item(Key={'appointmentId': appt_id})
            
            if 'Item' not in response:
                return {"error": "Appointment not found."}
            
            appt = response['Item']
            
            # Verify ownership
            if appt.get('patientId') != patient_id:
                return {"error": "This appointment does not belong to you."}
            
            # Update status to confirmed
            self.appointments_table.update_item(
                Key={'appointmentId': appt_id},
                UpdateExpression="SET #status = :confirmed, confirmedAt = :now",
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':confirmed': APPT_STATUS_CONFIRMED,
                    ':now': datetime.datetime.utcnow().isoformat() + 'Z'
                }
            )
            
            # Audit log
            self.audit_logger.log_phi_access(
                user_id=patient_id,
                session_id=session_id,
                resource_type='APPOINTMENT',
                resource_id=appt_id,
                action='CONFIRM',
                reason='Appointment confirmation'
            )
            
            return {
                "confirmed": True,
                "appointmentId": appt_id,
                "appointmentDetails": self.convert_decimals(appt),
                "message": "Appointment confirmed. We look forward to seeing you!"
            }
            
        except Exception as e:
            return {"error": str(e)}


class LookupAppointmentTool(BaseTool):
    """Look up patient appointments"""
    
    def __init__(self, dynamodb, appointments_table, session_manager, audit_logger):
        super().__init__(dynamodb)
        self.appointments_table = appointments_table
        self.session_manager = session_manager
        self.audit_logger = audit_logger
    
    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Look up appointments for a patient
        
        Args:
            patientId: Patient ID
            sessionId: Session identifier
            includeHistory: Include past appointments (default: False)
            
        Returns:
            appointments: List of appointments
            count: Number found
        """
        try:
            patient_id = content_data.get("patientId")
            session_id = content_data.get("sessionId")
            include_history = content_data.get("includeHistory", False)
            
            if not all([patient_id, session_id]):
                return {"error": "patientId and sessionId are required."}
            
            # Verify session
            if self.session_manager.requires_verification(session_id, required_level=1):
                return {"error": "Identity verification required."}
            
            # Query appointments
            today = datetime.datetime.now().strftime('%Y-%m-%d')
            
            if include_history:
                # All appointments
                response = self.appointments_table.scan(
                    FilterExpression="patientId = :pid",
                    ExpressionAttributeValues={':pid': patient_id}
                )
            else:
                # Upcoming only
                response = self.appointments_table.scan(
                    FilterExpression="patientId = :pid AND #date >= :today AND #status <> :cancelled",
                    ExpressionAttributeNames={'#date': 'date', '#status': 'status'},
                    ExpressionAttributeValues={
                        ':pid': patient_id,
                        ':today': today,
                        ':cancelled': APPT_STATUS_CANCELLED
                    }
                )
            
            appointments = response.get('Items', [])
            
            # Sort by date
            appointments.sort(key=lambda x: (x.get('date', ''), x.get('startTime', '')))
            
            # Convert decimals
            appointments = [self.convert_decimals(appt) for appt in appointments]
            
            # Audit log
            self.audit_logger.log_phi_access(
                user_id=patient_id,
                session_id=session_id,
                resource_type='APPOINTMENT',
                resource_id='MULTIPLE',
                action='READ',
                reason='Looking up patient appointments'
            )
            
            return {
                "success": True,
                "appointments": appointments,
                "count": len(appointments),
                "message": f"Found {len(appointments)} appointment(s)."
            }
            
        except Exception as e:
            return {"error": str(e)}
