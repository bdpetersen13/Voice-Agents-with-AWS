"""
Base Tool Class
Provides common functionality for all hotel tools
"""
from typing import Dict, Any
from decimal import Decimal


class BaseTool:
    """Base class for all hotel tools with common patterns"""

    def __init__(self, dynamodb):
        """
        Initialize base tool

        Args:
            dynamodb: DynamoDB resource
        """
        self.dynamodb = dynamodb

    def convert_decimals(self, obj: Any) -> Any:
        """
        Convert DynamoDB Decimal types to strings for JSON serialization

        Args:
            obj: Object to convert (can be dict, list, or Decimal)

        Returns:
            Converted object with Decimals as strings
        """
        if isinstance(obj, list):
            return [self.convert_decimals(i) for i in obj]
        elif isinstance(obj, dict):
            return {k: self.convert_decimals(v) for k, v in obj.items()}
        elif isinstance(obj, Decimal):
            return str(obj)
        else:
            return obj

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool logic. Must be implemented by subclasses.

        Args:
            content_data: Tool input parameters

        Returns:
            Tool execution result
        """
        raise NotImplementedError("Subclasses must implement execute()")
