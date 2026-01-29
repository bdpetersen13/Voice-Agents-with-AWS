"""
Reservation Tools
Tools for managing restaurant reservations
"""
import datetime
import random
from typing import Dict, Any
from boto3.dynamodb.conditions import Attr
from tools.base_tool import BaseTool
from config.constants import TABLE_RESERVATIONS, TABLE_CUSTOMERS, TABLE_TABLES, RESERVATION_ID_PREFIX


class LookupReservationTool(BaseTool):
    """
    Lookup reservation by phone number, name, or reservation ID.
    Handles "I don't remember the name" cases.
    """

    def __init__(self, dynamodb):
        super().__init__(dynamodb)
        self.reservations_table = dynamodb.Table(TABLE_RESERVATIONS)

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            phone = content_data.get("phone")
            customer_name = content_data.get("customerName")
            reservation_id = content_data.get("reservationId")

            # Priority 1: Direct reservation ID lookup
            if reservation_id:
                response = self.reservations_table.get_item(Key={'reservationId': reservation_id})
                if 'Item' in response:
                    reservation = self.convert_decimals(response['Item'])
                    return {
                        "found": True,
                        "reservations": [reservation],
                        "count": 1,
                        "lookupMethod": "reservationId"
                    }

            # Priority 2: Phone number lookup (handles "forgot name" case)
            if phone:
                response = self.reservations_table.scan(
                    FilterExpression=Attr('phone').eq(phone) & Attr('status').is_in(['Confirmed', 'Seated'])
                )
                reservations = response.get('Items', [])
                if reservations:
                    reservations = self.convert_decimals(reservations)
                    # Sort by date/time
                    reservations.sort(key=lambda x: x.get('reservationDateTime', ''))
                    return {
                        "found": True,
                        "reservations": reservations,
                        "count": len(reservations),
                        "lookupMethod": "phone",
                        "message": f"Found {len(reservations)} reservation(s) for this phone number."
                    }

            # Priority 3: Name lookup (partial match supported)
            if customer_name:
                response = self.reservations_table.scan(
                    FilterExpression=Attr('status').is_in(['Confirmed', 'Seated'])
                )
                all_reservations = response.get('Items', [])

                # Fuzzy match on name
                name_lower = customer_name.lower()
                matching = [r for r in all_reservations if name_lower in r.get('customerName', '').lower()]

                if matching:
                    matching = self.convert_decimals(matching)
                    matching.sort(key=lambda x: x.get('reservationDateTime', ''))
                    return {
                        "found": True,
                        "reservations": matching,
                        "count": len(matching),
                        "lookupMethod": "name",
                        "message": f"Found {len(matching)} reservation(s) matching '{customer_name}'."
                    }

            return {
                "found": False,
                "message": "No reservations found. Can you provide your phone number or reservation confirmation number?"
            }

        except Exception as e:
            return {"error": str(e)}


class CreateReservationTool(BaseTool):
    """
    Create a new reservation with party metadata.
    If time slot unavailable, suggest joining waitlist.
    """

    def __init__(self, dynamodb):
        super().__init__(dynamodb)
        self.reservations_table = dynamodb.Table(TABLE_RESERVATIONS)
        self.customers_table = dynamodb.Table(TABLE_CUSTOMERS)
        self.tables_table = dynamodb.Table(TABLE_TABLES)

    def _find_available_table(self, party_size, preferences):
        """
        Find available table matching party size and preferences.
        Returns None if no suitable table found.
        """
        from config.constants import TABLE_CAPACITY_BUFFER

        # Get all tables
        response = self.tables_table.scan()
        tables = response.get('Items', [])

        # Filter by capacity (table must fit party, but not be too large)
        suitable_tables = [t for t in tables if t['capacity'] >= party_size and t['capacity'] <= party_size + TABLE_CAPACITY_BUFFER]

        if not suitable_tables:
            return None

        # Apply preference filtering
        high_chair_needed = preferences.get('highChairNeeded', False)
        accessibility_needed = preferences.get('accessibilityNeeded', False)
        seating_preference = preferences.get('seatingPreference')

        # Filter by requirements
        if high_chair_needed:
            suitable_tables = [t for t in suitable_tables if t.get('hasHighChair', False)]
        if accessibility_needed:
            suitable_tables = [t for t in suitable_tables if t.get('isAccessible', False)]

        if not suitable_tables:
            return None

        # Try to match seating preference
        if seating_preference:
            preferred_tables = [t for t in suitable_tables if t.get('location') == seating_preference]
            if preferred_tables:
                suitable_tables = preferred_tables

        # Return first available table (in production, check reservation conflicts)
        for table in suitable_tables:
            if table.get('status') == 'Available':
                return table

        return None

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            customer_name = content_data.get("customerName")
            phone = content_data.get("phone")
            party_size = content_data.get("partySize")
            reservation_date = content_data.get("reservationDate")  # YYYY-MM-DD
            reservation_time = content_data.get("reservationTime")  # "7:00 PM"
            high_chair_needed = content_data.get("highChairNeeded", False)
            accessibility_needed = content_data.get("accessibilityNeeded", False)
            seating_preference = content_data.get("seatingPreference")  # Window, Patio, Main Dining, Private Room
            special_requests = content_data.get("specialRequests")

            # Validate required fields
            if not all([customer_name, phone, party_size, reservation_date, reservation_time]):
                return {"error": "Missing required fields: customerName, phone, partySize, reservationDate, reservationTime"}

            # Find suitable table
            preferences = {
                'highChairNeeded': high_chair_needed,
                'accessibilityNeeded': accessibility_needed,
                'seatingPreference': seating_preference
            }

            table = self._find_available_table(party_size, preferences)

            if not table:
                # No table available - suggest waitlist
                return {
                    "success": False,
                    "reason": "No tables available for that time",
                    "message": f"Unfortunately, we don't have availability for a party of {party_size} at {reservation_time} on {reservation_date}. Would you like to join the waitlist for this time?",
                    "suggestWaitlist": True,
                    "requestedDate": reservation_date,
                    "requestedTime": reservation_time
                }

            # Create reservation
            reservation_id = f"{RESERVATION_ID_PREFIX}-{datetime.datetime.now().strftime('%Y%m%d')}-{random.randint(100, 999):03d}"

            # Try to find existing customer
            customer_id = None
            customer_response = self.customers_table.scan(FilterExpression=Attr('phone').eq(phone))
            if customer_response.get('Items'):
                customer_id = customer_response['Items'][0]['customerId']

            # Combine date and time into ISO datetime
            try:
                time_obj = datetime.datetime.strptime(reservation_time, "%I:%M %p").time()
                date_obj = datetime.datetime.strptime(reservation_date, "%Y-%m-%d").date()
                reservation_datetime = datetime.datetime.combine(date_obj, time_obj).isoformat()
            except:
                reservation_datetime = None

            reservation = {
                'reservationId': reservation_id,
                'customerId': customer_id,
                'customerName': customer_name,
                'phone': phone,
                'partySize': party_size,
                'reservationDate': reservation_date,
                'reservationTime': reservation_time,
                'reservationDateTime': reservation_datetime,
                'tableId': table['tableId'],
                'status': 'Confirmed',
                'specialRequests': special_requests,
                'highChairNeeded': high_chair_needed,
                'accessibilityNeeded': accessibility_needed,
                'seatingPreference': seating_preference,
                'createdAt': datetime.datetime.now().isoformat(),
                'notificationSent': False
            }

            self.reservations_table.put_item(Item=reservation)

            return {
                "success": True,
                "reservationId": reservation_id,
                "tableId": table['tableId'],
                "tableLocation": table.get('location'),
                "customerName": customer_name,
                "partySize": party_size,
                "reservationDate": reservation_date,
                "reservationTime": reservation_time,
                "message": f"Reservation confirmed! Your confirmation number is {reservation_id}. We'll see you on {reservation_date} at {reservation_time} for a party of {party_size}. Your table is {table['tableId']} in the {table.get('location')} section."
            }

        except Exception as e:
            return {"error": str(e)}


class EditReservationTool(BaseTool):
    """
    Edit an existing reservation (party size, time, special requests).
    """

    def __init__(self, dynamodb):
        super().__init__(dynamodb)
        self.reservations_table = dynamodb.Table(TABLE_RESERVATIONS)

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            reservation_id = content_data.get("reservationId")
            phone = content_data.get("phone")  # Alternative lookup method

            # Validate we have a way to find the reservation
            if not reservation_id and not phone:
                return {"error": "Either reservationId or phone is required to edit a reservation."}

            # Lookup reservation
            if reservation_id:
                response = self.reservations_table.get_item(Key={'reservationId': reservation_id})
                if 'Item' not in response:
                    return {"found": False, "message": "Reservation not found."}
                reservation = response['Item']
            else:
                # Lookup by phone
                response = self.reservations_table.scan(
                    FilterExpression=Attr('phone').eq(phone) & Attr('status').eq('Confirmed')
                )
                reservations = response.get('Items', [])
                if not reservations:
                    return {"found": False, "message": "No confirmed reservations found for this phone number."}
                reservation = reservations[0]  # Take most recent
                reservation_id = reservation['reservationId']

            # Check if reservation can be edited
            if reservation['status'] not in ['Confirmed', 'Seated']:
                return {
                    "success": False,
                    "message": f"This reservation cannot be edited (status: {reservation['status']})."
                }

            # Apply updates
            update_expression_parts = []
            expression_attribute_values = {}
            expression_attribute_names = {}

            new_party_size = content_data.get("newPartySize")
            new_date = content_data.get("newReservationDate")
            new_time = content_data.get("newReservationTime")
            new_special_requests = content_data.get("newSpecialRequests")
            new_seating_preference = content_data.get("newSeatingPreference")

            changes = []

            if new_party_size is not None:
                update_expression_parts.append("partySize = :partySize")
                expression_attribute_values[':partySize'] = new_party_size
                changes.append(f"party size changed to {new_party_size}")

            if new_date:
                update_expression_parts.append("reservationDate = :date")
                expression_attribute_values[':date'] = new_date
                changes.append(f"date changed to {new_date}")

            if new_time:
                update_expression_parts.append("reservationTime = :time")
                expression_attribute_values[':time'] = new_time
                changes.append(f"time changed to {new_time}")

            if new_special_requests is not None:
                update_expression_parts.append("specialRequests = :requests")
                expression_attribute_values[':requests'] = new_special_requests
                changes.append("special requests updated")

            if new_seating_preference:
                update_expression_parts.append("seatingPreference = :pref")
                expression_attribute_values[':pref'] = new_seating_preference
                changes.append(f"seating preference changed to {new_seating_preference}")

            if not update_expression_parts:
                return {"success": False, "message": "No changes specified."}

            # Update reservation
            update_expression = "SET " + ", ".join(update_expression_parts)

            self.reservations_table.update_item(
                Key={'reservationId': reservation_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values
            )

            return {
                "success": True,
                "reservationId": reservation_id,
                "changes": changes,
                "message": f"Reservation {reservation_id} updated successfully: {', '.join(changes)}."
            }

        except Exception as e:
            return {"error": str(e)}


class CancelReservationTool(BaseTool):
    """
    Cancel a reservation by ID or phone number.
    """

    def __init__(self, dynamodb):
        super().__init__(dynamodb)
        self.reservations_table = dynamodb.Table(TABLE_RESERVATIONS)

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            reservation_id = content_data.get("reservationId")
            phone = content_data.get("phone")

            if not reservation_id and not phone:
                return {"error": "Either reservationId or phone is required to cancel a reservation."}

            # Lookup reservation
            if reservation_id:
                response = self.reservations_table.get_item(Key={'reservationId': reservation_id})
                if 'Item' not in response:
                    return {"found": False, "message": "Reservation not found."}
                reservation = response['Item']
            else:
                response = self.reservations_table.scan(
                    FilterExpression=Attr('phone').eq(phone) & Attr('status').eq('Confirmed')
                )
                reservations = response.get('Items', [])
                if not reservations:
                    return {"found": False, "message": "No confirmed reservations found for this phone number."}
                reservation = reservations[0]
                reservation_id = reservation['reservationId']

            # Cancel the reservation
            self.reservations_table.update_item(
                Key={'reservationId': reservation_id},
                UpdateExpression="SET #status = :cancelled, cancelledAt = :now",
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':cancelled': 'Cancelled',
                    ':now': datetime.datetime.now().isoformat()
                }
            )

            return {
                "success": True,
                "reservationId": reservation_id,
                "customerName": reservation.get('customerName'),
                "reservationDate": reservation.get('reservationDate'),
                "reservationTime": reservation.get('reservationTime'),
                "message": f"Reservation {reservation_id} for {reservation.get('customerName')} on {reservation.get('reservationDate')} at {reservation.get('reservationTime')} has been cancelled."
            }

        except Exception as e:
            return {"error": str(e)}


class ConfirmReservationTool(BaseTool):
    """
    Confirm that a reservation exists and provide details.
    """

    def __init__(self, dynamodb):
        super().__init__(dynamodb)
        self.reservations_table = dynamodb.Table(TABLE_RESERVATIONS)

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            reservation_id = content_data.get("reservationId")
            phone = content_data.get("phone")

            if not reservation_id and not phone:
                return {"error": "Either reservationId or phone is required."}

            # Lookup reservation
            if reservation_id:
                response = self.reservations_table.get_item(Key={'reservationId': reservation_id})
                if 'Item' not in response:
                    return {"found": False, "message": "Reservation not found."}
                reservation = self.convert_decimals(response['Item'])
            else:
                response = self.reservations_table.scan(
                    FilterExpression=Attr('phone').eq(phone) & Attr('status').eq('Confirmed')
                )
                reservations = response.get('Items', [])
                if not reservations:
                    return {"found": False, "message": "No confirmed reservations found for this phone number."}
                reservation = self.convert_decimals(reservations[0])

            return {
                "confirmed": True,
                "reservation": reservation,
                "message": f"Yes, we have your reservation for {reservation.get('customerName')} on {reservation.get('reservationDate')} at {reservation.get('reservationTime')} for a party of {reservation.get('partySize')}. Your confirmation number is {reservation.get('reservationId')}."
            }

        except Exception as e:
            return {"error": str(e)}
