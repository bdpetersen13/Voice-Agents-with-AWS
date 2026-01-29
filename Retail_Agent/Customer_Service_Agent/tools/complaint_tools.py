"""
Complaint Tools
Tools for logging customer complaints
"""
import datetime
import random
from typing import Dict, Any
from tools.base_tool import BaseTool


class FileComplaintTool(BaseTool):
    """Log a customer complaint for tracking and follow-up"""

    def __init__(self, dynamodb, service_requests_table):
        super().__init__(dynamodb)
        self.service_requests_table = service_requests_table

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Log a customer complaint for tracking and follow-up"""
        try:
            member_id = content_data.get("memberId")
            complaint_description = content_data.get("description")

            if not all([member_id, complaint_description]):
                return {"error": "memberId and description are required."}

            # Generate request ID
            request_id = f"REQ-{datetime.date.today().strftime('%Y%m%d')}-{random.randint(10000, 99999)}"

            self.service_requests_table.put_item(Item={
                'requestId': request_id,
                'memberId': member_id,
                'requestType': 'Complaint',
                'description': complaint_description,
                'status': 'Open',
                'createdDate': datetime.datetime.now().isoformat(),
                'resolvedDate': None,
                'resolution': ''
            })

            return {
                "success": True,
                "requestId": request_id,
                "message": f"Complaint logged successfully. A manager will review your concern within 24 hours. Your reference number is {request_id}."
            }

        except Exception as e:
            return {"error": str(e)}
