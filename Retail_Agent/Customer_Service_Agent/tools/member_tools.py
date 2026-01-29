"""
Member Tools
Tools for member verification and membership management
"""
from typing import Dict, Any
from tools.base_tool import BaseTool


class VerifyMemberTool(BaseTool):
    """Verify member identity via scanned barcode"""

    def __init__(self, dynamodb, members_table):
        super().__init__(dynamodb)
        self.members_table = members_table

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify member identity via scanned barcode.
        In production, memberId comes from barcode scanner at kiosk.
        """
        try:
            member_id = content_data.get("memberId")
            if not member_id:
                return {"error": "memberId is required (from barcode scan)."}

            response = self.members_table.get_item(Key={'memberId': member_id})

            if 'Item' not in response:
                return {
                    "verified": False,
                    "message": "Member not found. Please scan again or visit the service desk."
                }

            item = response['Item']

            # Check membership status
            if item.get('membershipStatus') != 'Active':
                return {
                    "verified": False,
                    "message": f"Membership status is {item.get('membershipStatus')}. Please visit the service desk."
                }

            return {
                "verified": True,
                "memberId": item['memberId'],
                "membershipType": item.get('membershipType'),
                "memberName": item.get('primaryMember', {}).get('name'),
                "rewardsBalance": str(item.get('rewardsBalance', '0.00')),
                "loyaltyPoints": item.get('loyaltyPoints', 0),
                "householdMembers": item.get('householdMembers', []),
                "message": f"Welcome back, {item.get('primaryMember', {}).get('name')}!"
            }
        except Exception as e:
            return {"error": str(e)}


class ModifyMembershipTool(BaseTool):
    """Update member contact information or payment method"""

    def __init__(self, dynamodb, members_table):
        super().__init__(dynamodb)
        self.members_table = members_table

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update member contact information or payment method.
        Supports: phone, email, address, paymentMethod
        """
        try:
            member_id = content_data.get("memberId")
            if not member_id:
                return {"error": "memberId is required."}

            # Build update expression dynamically
            update_parts = []
            expr_values = {}

            # Phone update
            new_phone = content_data.get("newPhone")
            if new_phone:
                update_parts.append("primaryMember.#phone = :phone")
                expr_values[":phone"] = new_phone

            # Email update
            new_email = content_data.get("newEmail")
            if new_email:
                update_parts.append("primaryMember.email = :email")
                expr_values[":email"] = new_email

            # Address update
            new_address = content_data.get("newAddress")
            if new_address:
                update_parts.append("primaryMember.address = :address")
                expr_values[":address"] = new_address

            # Payment method update
            new_payment = content_data.get("newPaymentMethod")
            if new_payment:
                update_parts.append("paymentMethod = :payment")
                expr_values[":payment"] = new_payment

            if not update_parts:
                return {
                    "error": "Nothing to update. Provide newPhone, newEmail, newAddress, or newPaymentMethod."
                }

            update_expression = "SET " + ", ".join(update_parts)
            expr_attr_names = {"#phone": "phone"} if new_phone else {}

            # Apply update
            kwargs = {
                'Key': {'memberId': member_id},
                'UpdateExpression': update_expression,
                'ExpressionAttributeValues': expr_values,
            }
            if expr_attr_names:
                kwargs['ExpressionAttributeNames'] = expr_attr_names

            self.members_table.update_item(**kwargs)

            # Fetch updated member
            response = self.members_table.get_item(Key={'memberId': member_id})
            updated_item = response.get("Item", {})

            changes = []
            if new_phone:
                changes.append(f"Phone updated to {new_phone}")
            if new_email:
                changes.append(f"Email updated to {new_email}")
            if new_address:
                changes.append("Address updated")
            if new_payment:
                changes.append("Payment method updated")

            return {
                "success": True,
                "message": f"Membership updated successfully. Changes: {', '.join(changes)}",
                "updatedMember": self.convert_decimals(updated_item)
            }

        except Exception as e:
            return {"error": str(e)}
