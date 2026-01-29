"""
Member Tools
Tools for member verification
"""
from typing import Dict, Any
from boto3.dynamodb.conditions import Attr
from tools.base_tool import BaseTool


class VerifyMemberTool(BaseTool):
    """Verify member by phone number or member ID"""

    def __init__(self, dynamodb, members_table):
        super().__init__(dynamodb)
        self.members_table = members_table

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify member by phone number or member ID.
        For call center, phone number is most common.
        """
        try:
            member_id = content_data.get("memberId")
            phone = content_data.get("phone")

            if not member_id and not phone:
                return {"error": "Either memberId or phone number is required."}

            # Direct lookup by member ID
            if member_id:
                response = self.members_table.get_item(Key={'memberId': member_id})
                if 'Item' in response:
                    member = response['Item']
                    return {
                        "verified": True,
                        "memberId": member['memberId'],
                        "name": member['name'],
                        "phone": member.get('phone'),
                        "email": member.get('email'),
                        "membershipType": member.get('membershipType'),
                        "message": f"Hello {member['name']}, how can I help you today?"
                    }

            # Scan by phone number
            if phone:
                # Normalize phone number
                phone_normalized = phone.replace('-', '').replace(' ', '').replace('(', '').replace(')', '')

                response = self.members_table.scan(
                    FilterExpression=Attr('phone').contains(phone_normalized[-4:])  # Last 4 digits
                )

                items = response.get('Items', [])
                if items:
                    member = items[0]  # Take first match
                    return {
                        "verified": True,
                        "memberId": member['memberId'],
                        "name": member['name'],
                        "phone": member.get('phone'),
                        "email": member.get('email'),
                        "membershipType": member.get('membershipType'),
                        "message": f"Hello {member['name']}, how can I help you today?"
                    }

            return {"verified": False, "message": "Member not found. Please verify the information and try again."}

        except Exception as e:
            return {"error": str(e)}
