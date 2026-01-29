"""
Seating Tools
Tools for managing guest seating
"""
import datetime
from typing import Dict, Any
from tools.base_tool import BaseTool
from config.constants import TABLE_RESERVATIONS, TABLE_WAITLIST


class SeatGuestTool(BaseTool):
    """
    Mark guest as seated (for reservation or waitlist).
    Updates reservation/waitlist status and table status.
    """

    def __init__(self, dynamodb):
        super().__init__(dynamodb)
        self.reservations_table = dynamodb.Table(TABLE_RESERVATIONS)
        self.waitlist_table = dynamodb.Table(TABLE_WAITLIST)

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            reservation_id = content_data.get("reservationId")
            waitlist_id = content_data.get("waitlistId")

            if not reservation_id and not waitlist_id:
                return {"error": "Either reservationId or waitlistId is required."}

            if reservation_id:
                # Seat from reservation
                response = self.reservations_table.get_item(Key={'reservationId': reservation_id})
                if 'Item' not in response:
                    return {"found": False, "message": "Reservation not found."}

                reservation = response['Item']

                self.reservations_table.update_item(
                    Key={'reservationId': reservation_id},
                    UpdateExpression="SET #status = :seated, seatedAt = :now",
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':seated': 'Seated',
                        ':now': datetime.datetime.now().isoformat()
                    }
                )

                return {
                    "success": True,
                    "customerName": reservation.get('customerName'),
                    "tableId": reservation.get('tableId'),
                    "message": f"{reservation.get('customerName')} has been seated at table {reservation.get('tableId')}."
                }

            else:
                # Seat from waitlist
                response = self.waitlist_table.get_item(Key={'waitlistId': waitlist_id})
                if 'Item' not in response:
                    return {"found": False, "message": "Waitlist entry not found."}

                entry = response['Item']

                self.waitlist_table.update_item(
                    Key={'waitlistId': waitlist_id},
                    UpdateExpression="SET #status = :seated, seatedAt = :now",
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':seated': 'Seated',
                        ':now': datetime.datetime.now().isoformat()
                    }
                )

                return {
                    "success": True,
                    "customerName": entry.get('customerName'),
                    "message": f"{entry.get('customerName')} from waitlist has been seated."
                }

        except Exception as e:
            return {"error": str(e)}
