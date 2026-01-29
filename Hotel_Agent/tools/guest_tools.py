"""
Guest Tools
Handles guest profile lookups and management
"""
from typing import Dict, Any
from tools.base_tool import BaseTool
from config.constants import *


class CheckGuestProfileTool(BaseTool):
    """Look up a guest profile by name"""

    def __init__(self, dynamodb, guests_table):
        super().__init__(dynamodb)
        self.guests_table = guests_table

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Look up a guest profile in Hotel_Guests by guestName.
        Used for identity verification and preferences.
        """
        try:
            guest_name = content_data.get("guestName")
            if not guest_name:
                return {"error": "guestName is required."}

            response = self.guests_table.get_item(Key={'guestName': guest_name})

            if 'Item' not in response:
                return {"found": False, "message": "Guest not found."}

            item = response['Item']

            return {
                "found": True,
                "guestName": item['guestName'],
                "dob": item.get('dob'),
                "loyaltyTier": item.get('loyaltyTier'),
                "phoneNumber": item.get('phoneNumber'),
                "email": item.get('email'),
                "preferredLanguage": item.get('preferredLanguage'),
                "preferredBedType": item.get('preferredBedType'),
                "preferredView": item.get('preferredView'),
                "vipFlag": bool(item.get('vipFlag', False))
            }
        except Exception as e:
            return {"error": str(e)}
