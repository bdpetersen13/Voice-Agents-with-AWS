"""
Waitlist Tools
Tools for managing restaurant waitlist
"""
import datetime
import random
from typing import Dict, Any
from boto3.dynamodb.conditions import Attr
from tools.base_tool import BaseTool
from config.constants import (
    TABLE_WAITLIST,
    TABLE_CUSTOMERS,
    TABLE_NOTIFICATIONS,
    WAITLIST_ID_PREFIX,
    NOTIFICATION_ID_PREFIX,
    WAIT_TIME_SMALL_PARTY,
    WAIT_TIME_MEDIUM_PARTY,
    WAIT_TIME_LARGE_PARTY,
    WAIT_TIME_XLARGE_PARTY,
)


class JoinWaitlistTool(BaseTool):
    """
    Add customer to waitlist for a fully booked time slot or walk-in.
    """

    def __init__(self, dynamodb):
        super().__init__(dynamodb)
        self.waitlist_table = dynamodb.Table(TABLE_WAITLIST)
        self.customers_table = dynamodb.Table(TABLE_CUSTOMERS)

    def _calculate_wait_time(self, party_size):
        """
        Calculate estimated wait time based on current occupancy.
        In production, this would analyze current table turnover rates.
        """
        if party_size <= 2:
            return random.randint(*WAIT_TIME_SMALL_PARTY)
        elif party_size <= 4:
            return random.randint(*WAIT_TIME_MEDIUM_PARTY)
        elif party_size <= 6:
            return random.randint(*WAIT_TIME_LARGE_PARTY)
        else:
            return random.randint(*WAIT_TIME_XLARGE_PARTY)

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            customer_name = content_data.get("customerName")
            phone = content_data.get("phone")
            party_size = content_data.get("partySize")
            requested_date = content_data.get("requestedDate")  # Optional for reservation waitlist
            requested_time = content_data.get("requestedTime")  # Optional for reservation waitlist
            high_chair_needed = content_data.get("highChairNeeded", False)
            accessibility_needed = content_data.get("accessibilityNeeded", False)
            seating_preference = content_data.get("seatingPreference")
            waitlist_type = content_data.get("type", "Walk-in")  # "Walk-in" or "Reservation Waitlist"

            # Validate required fields
            if not all([customer_name, phone, party_size]):
                return {"error": "Missing required fields: customerName, phone, partySize"}

            # Create waitlist entry
            waitlist_id = f"{WAITLIST_ID_PREFIX}-{datetime.datetime.now().strftime('%Y%m%d')}-{random.randint(100, 999):03d}"

            # Calculate estimated wait for walk-ins
            estimated_wait = None
            if waitlist_type == "Walk-in":
                estimated_wait = self._calculate_wait_time(party_size)

            # Try to find existing customer
            customer_id = None
            customer_response = self.customers_table.scan(FilterExpression=Attr('phone').eq(phone))
            if customer_response.get('Items'):
                customer_id = customer_response['Items'][0]['customerId']

            waitlist_entry = {
                'waitlistId': waitlist_id,
                'customerId': customer_id,
                'customerName': customer_name,
                'phone': phone,
                'partySize': party_size,
                'requestedDate': requested_date or datetime.date.today().strftime('%Y-%m-%d'),
                'requestedTime': requested_time,
                'type': waitlist_type,
                'status': 'Waiting',
                'estimatedWaitMinutes': estimated_wait,
                'quotedAt': datetime.datetime.now().isoformat(),
                'highChairNeeded': high_chair_needed,
                'accessibilityNeeded': accessibility_needed,
                'seatingPreference': seating_preference,
                'notificationSent': False
            }

            self.waitlist_table.put_item(Item=waitlist_entry)

            message = f"You've been added to the waitlist, {customer_name}. Your waitlist number is {waitlist_id}."
            if estimated_wait:
                message += f" Estimated wait time is {estimated_wait} minutes."
            if waitlist_type == "Reservation Waitlist":
                message += f" We'll call you at {phone} if a table opens up for {requested_time} on {requested_date}."

            return {
                "success": True,
                "waitlistId": waitlist_id,
                "estimatedWaitMinutes": estimated_wait,
                "type": waitlist_type,
                "message": message
            }

        except Exception as e:
            return {"error": str(e)}


class CheckWaitTimeTool(BaseTool):
    """
    Quote current wait time for walk-in guests.
    """

    def __init__(self, dynamodb):
        super().__init__(dynamodb)

    def _calculate_wait_time(self, party_size):
        """Calculate wait time based on party size"""
        if party_size <= 2:
            return random.randint(*WAIT_TIME_SMALL_PARTY)
        elif party_size <= 4:
            return random.randint(*WAIT_TIME_MEDIUM_PARTY)
        elif party_size <= 6:
            return random.randint(*WAIT_TIME_LARGE_PARTY)
        else:
            return random.randint(*WAIT_TIME_XLARGE_PARTY)

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            party_size = content_data.get("partySize")

            if not party_size:
                return {"error": "partySize is required to check wait time."}

            # Calculate wait time
            estimated_wait = self._calculate_wait_time(party_size)

            return {
                "estimatedWaitMinutes": estimated_wait,
                "partySize": party_size,
                "message": f"Current wait time for a party of {party_size} is approximately {estimated_wait} minutes."
            }

        except Exception as e:
            return {"error": str(e)}


class NotifyTableReadyTool(BaseTool):
    """
    Automatically notify guest when table is ready (for waitlist).
    Creates notification entry that would trigger SMS/call in production.
    """

    def __init__(self, dynamodb):
        super().__init__(dynamodb)
        self.waitlist_table = dynamodb.Table(TABLE_WAITLIST)
        self.notifications_table = dynamodb.Table(TABLE_NOTIFICATIONS)

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            waitlist_id = content_data.get("waitlistId")

            if not waitlist_id:
                return {"error": "waitlistId is required."}

            # Get waitlist entry
            response = self.waitlist_table.get_item(Key={'waitlistId': waitlist_id})
            if 'Item' not in response:
                return {"found": False, "message": "Waitlist entry not found."}

            entry = response['Item']

            # Create notification
            notification_id = f"{NOTIFICATION_ID_PREFIX}-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            notification = {
                'notificationId': notification_id,
                'waitlistId': waitlist_id,
                'phone': entry['phone'],
                'customerName': entry['customerName'],
                'message': f"Your table for {entry['partySize']} is ready! Please come to the host stand.",
                'status': 'Pending',
                'createdAt': datetime.datetime.now().isoformat(),
                'sentAt': None
            }

            self.notifications_table.put_item(Item=notification)

            # Update waitlist entry
            self.waitlist_table.update_item(
                Key={'waitlistId': waitlist_id},
                UpdateExpression="SET notificationSent = :true, #status = :ready",
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':true': True,
                    ':ready': 'Table Ready'
                }
            )

            return {
                "success": True,
                "notificationId": notification_id,
                "customerName": entry['customerName'],
                "phone": entry['phone'],
                "message": f"Table ready notification sent to {entry['customerName']} at {entry['phone']}."
            }

        except Exception as e:
            return {"error": str(e)}
