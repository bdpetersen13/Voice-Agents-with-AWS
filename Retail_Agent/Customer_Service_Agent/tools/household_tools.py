"""
Household Tools
Tools for managing household members on a membership
"""
from typing import Dict, Any
from tools.base_tool import BaseTool


class AddHouseholdMemberTool(BaseTool):
    """Add a household member to the membership"""

    def __init__(self, dynamodb, members_table):
        super().__init__(dynamodb)
        self.members_table = members_table

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a household member to the membership"""
        try:
            member_id = content_data.get("memberId")
            household_member = content_data.get("householdMember")

            if not member_id or not household_member:
                return {
                    "error": "memberId and householdMember (with name, dob, relationship) are required."
                }

            # Validate household member structure
            required_fields = ["name", "dob", "relationship"]
            if not all(field in household_member for field in required_fields):
                return {
                    "error": "householdMember must include name, dob, and relationship."
                }

            # Add to list
            self.members_table.update_item(
                Key={'memberId': member_id},
                UpdateExpression="SET householdMembers = list_append(if_not_exists(householdMembers, :empty_list), :member)",
                ExpressionAttributeValues={
                    ":member": [household_member],
                    ":empty_list": []
                }
            )

            return {
                "success": True,
                "message": f"Successfully added {household_member['name']} as a household member."
            }

        except Exception as e:
            return {"error": str(e)}


class RemoveHouseholdMemberTool(BaseTool):
    """Remove a household member by name"""

    def __init__(self, dynamodb, members_table):
        super().__init__(dynamodb)
        self.members_table = members_table

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove a household member by name"""
        try:
            member_id = content_data.get("memberId")
            household_member_name = content_data.get("householdMemberName")

            if not member_id or not household_member_name:
                return {
                    "error": "memberId and householdMemberName are required."
                }

            # Fetch current household members
            response = self.members_table.get_item(Key={'memberId': member_id})
            if 'Item' not in response:
                return {"error": "Member not found."}

            household_members = response['Item'].get('householdMembers', [])

            # Find and remove the member
            updated_members = [
                m for m in household_members 
                if m.get('name') != household_member_name
            ]

            if len(updated_members) == len(household_members):
                return {
                    "error": f"Household member '{household_member_name}' not found."
                }

            # Update the list
            self.members_table.update_item(
                Key={'memberId': member_id},
                UpdateExpression="SET householdMembers = :members",
                ExpressionAttributeValues={":members": updated_members}
            )

            return {
                "success": True,
                "message": f"Successfully removed {household_member_name} from the membership."
            }

        except Exception as e:
            return {"error": str(e)}
