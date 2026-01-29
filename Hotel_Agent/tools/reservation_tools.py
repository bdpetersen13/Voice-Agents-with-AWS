"""
Reservation Tools
Handles reservation lookups and updates
"""
import datetime
from decimal import Decimal
from typing import Dict, Any
from boto3.dynamodb.conditions import Attr
from tools.base_tool import BaseTool
from config.constants import *


class CheckReservationStatusTool(BaseTool):
    """Check upcoming and past reservations for a guest"""

    def __init__(self, dynamodb, reservations_table):
        super().__init__(dynamodb)
        self.reservations_table = reservations_table

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check upcoming and (optionally) past reservations in Hotel_Reservations
        for a given guest.
        """
        try:
            guest_name = content_data.get("guestName")
            include_past = content_data.get("includePastStays", False)

            if not guest_name:
                return {"error": "guestName is required."}

            today_str = datetime.date.today().strftime(DATE_FORMAT)

            # Find all reservations for this guest
            filter_expression = Attr('guestName').eq(guest_name)
            response = self.reservations_table.scan(FilterExpression=filter_expression)
            items = response.get('Items', [])

            if not items:
                return {
                    "found": False,
                    "message": "No reservations found for this guest."
                }

            # Separate upcoming/current vs past stays
            upcoming = []
            past = []

            for r in items:
                check_out = r.get('checkOutDate', '')
                status = r.get('status', '')
                # Normalize Decimal -> string for balanceDue
                r = self.convert_decimals(r)

                if check_out >= today_str and status in ["Confirmed", "CheckedIn"]:
                    upcoming.append(r)
                else:
                    past.append(r)

            # Sort upcoming by checkInDate
            upcoming.sort(key=lambda x: x.get('checkInDate', '9999-99-99'))

            upcoming_res = upcoming[0] if upcoming else None
            past_stays = past if include_past else []

            message_parts = []
            if upcoming_res:
                msg = (
                    f"You have an upcoming stay in room {upcoming_res.get('roomNumber')} "
                    f"({upcoming_res.get('roomType')}) from "
                    f"{upcoming_res.get('checkInDate')} to {upcoming_res.get('checkOutDate')}."
                )
                if upcoming_res.get('paymentStatus') != "Paid":
                    msg += f" Your current balance due is {upcoming_res.get('balanceDue', '0.00')}."
                message_parts.append(msg)
            else:
                message_parts.append("You have no upcoming reservations.")

            if include_past and past_stays:
                message_parts.append(f"I also found {len(past_stays)} past stay(s).")

            return {
                "found": True,
                "upcomingReservation": upcoming_res,
                "pastStays": past_stays,
                "message": " ".join(message_parts)
            }

        except Exception as e:
            return {"error": str(e)}


class UpdateReservationTool(BaseTool):
    """Update a reservation's room type and/or special requests"""

    def __init__(self, dynamodb, reservations_table):
        super().__init__(dynamodb)
        self.reservations_table = reservations_table

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a reservation's room type and/or special requests in Hotel_Reservations.
        - reservationId: required
        - newRoomType: optional string
        - newSpecialRequest: optional string (appended to specialRequests list)
        """
        try:
            reservation_id = content_data.get("reservationId")
            new_room_type = content_data.get("newRoomType")
            new_special_request = content_data.get("newSpecialRequest")

            if not reservation_id:
                return {"error": "reservationId is required."}

            # Build dynamic update expression
            update_parts = []
            expr_values = {}

            if new_room_type:
                update_parts.append("roomType = :rt")
                expr_values[":rt"] = new_room_type

            if new_special_request:
                update_parts.append(
                    "specialRequests = list_append("
                    "if_not_exists(specialRequests, :empty_list), :sr)"
                )
                expr_values[":sr"] = [new_special_request]
                expr_values[":empty_list"] = []

            if not update_parts:
                return {
                    "error": "Nothing to update. Provide newRoomType and/or newSpecialRequest."
                }

            update_expression = "SET " + ", ".join(update_parts)

            # Apply update
            self.reservations_table.update_item(
                Key={'reservationId': reservation_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expr_values
            )

            # Fetch updated reservation to return full context
            response = self.reservations_table.get_item(
                Key={'reservationId': reservation_id}
            )
            updated_item = response.get("Item", {})

            # Convert Decimal to string
            updated_item = self.convert_decimals(updated_item)

            msg_parts = [f"Reservation {reservation_id} has been updated."]
            if new_room_type:
                msg_parts.append(f"New room type: {new_room_type}.")
            if new_special_request:
                msg_parts.append(f"Added special request: '{new_special_request}'.")

            return {
                "success": True,
                "message": " ".join(msg_parts),
                "updatedReservation": updated_item
            }

        except Exception as e:
            return {"error": str(e)}
