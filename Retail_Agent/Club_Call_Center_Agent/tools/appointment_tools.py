"""
Appointment Tools
Tools for scheduling and checking appointments
"""
import random
from typing import Dict, Any
from boto3.dynamodb.conditions import Attr
from tools.base_tool import BaseTool


class ScheduleAppointmentTool(BaseTool):
    """Schedule an appointment at Tire, Optical, Hearing, or Pharmacy"""

    def __init__(self, dynamodb, appointments_table):
        super().__init__(dynamodb)
        self.appointments_table = appointments_table

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Schedule an appointment at Tire Center, Optical, Hearing Aid, or Pharmacy.
        """
        try:
            member_id = content_data.get("memberId")
            member_name = content_data.get("memberName")
            department = content_data.get("department")  # TireCenter, OpticalCenter, HearingAidCenter, Pharmacy
            service_type = content_data.get("serviceType")
            appointment_date = content_data.get("appointmentDate")
            appointment_time = content_data.get("appointmentTime")
            notes = content_data.get("notes", "")

            if not all([member_id, department, service_type, appointment_date, appointment_time]):
                return {"error": "memberId, department, serviceType, appointmentDate, and appointmentTime are required."}

            # Generate appointment ID and confirmation number
            appt_id = f"APPT-{department[:4].upper()}-{appointment_date.replace('-', '')}-{random.randint(100, 999)}"
            confirmation = f"{department[:4].upper()}-{random.randint(10000, 99999)}"

            # Create appointment
            self.appointments_table.put_item(Item={
                'appointmentId': appt_id,
                'memberId': member_id,
                'memberName': member_name or "Member",
                'department': department,
                'serviceType': service_type,
                'appointmentDate': appointment_date,
                'appointmentTime': appointment_time,
                'duration': '1 hour',  # Default
                'status': 'Confirmed',
                'notes': notes,
                'confirmationNumber': confirmation
            })

            return {
                "success": True,
                "appointmentId": appt_id,
                "confirmationNumber": confirmation,
                "message": f"Appointment scheduled successfully! {department} - {service_type} on {appointment_date} at {appointment_time}. Your confirmation number is {confirmation}."
            }

        except Exception as e:
            return {"error": str(e)}


class CheckAppointmentTool(BaseTool):
    """Check existing appointment by confirmation number or member ID"""

    def __init__(self, dynamodb, appointments_table):
        super().__init__(dynamodb)
        self.appointments_table = appointments_table

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check existing appointment by confirmation number or member ID.
        """
        try:
            confirmation_number = content_data.get("confirmationNumber")
            member_id = content_data.get("memberId")
            department = content_data.get("department")

            if not confirmation_number and not member_id:
                return {"error": "Either confirmationNumber or memberId is required."}

            # Search by confirmation number
            if confirmation_number:
                response = self.appointments_table.scan(
                    FilterExpression=Attr('confirmationNumber').eq(confirmation_number)
                )

                items = response.get('Items', [])
                if not items:
                    return {"found": False, "message": "Appointment not found with that confirmation number."}

                appt = self.convert_decimals(items[0])
                status = appt.get('status')
                date = appt.get('appointmentDate')
                time = appt.get('appointmentTime')
                dept = appt.get('department')
                service = appt.get('serviceType')

                if status == 'Ready':
                    return {
                        "found": True,
                        "appointment": appt,
                        "message": f"Your {dept} appointment for {service} is ready! Confirmation: {confirmation_number}"
                    }
                else:
                    return {
                        "found": True,
                        "appointment": appt,
                        "message": f"Your {dept} appointment for {service} is scheduled for {date} at {time}. Confirmation: {confirmation_number}"
                    }

            # Search by member ID
            if member_id:
                filter_expr = Attr('memberId').eq(member_id)
                if department:
                    filter_expr = filter_expr & Attr('department').eq(department)

                response = self.appointments_table.scan(FilterExpression=filter_expr)

                items = response.get('Items', [])
                if not items:
                    return {"found": False, "message": "No appointments found for this member."}

                # Sort by date (most recent first)
                items.sort(key=lambda x: x.get('appointmentDate', ''), reverse=True)
                appt = self.convert_decimals(items[0])

                return {
                    "found": True,
                    "appointment": appt,
                    "message": f"Your most recent appointment: {appt.get('department')} - {appt.get('serviceType')} on {appt.get('appointmentDate')} at {appt.get('appointmentTime')}. Confirmation: {appt.get('confirmationNumber')}"
                }

            return {"found": False, "message": "Appointment not found."}

        except Exception as e:
            return {"error": str(e)}
