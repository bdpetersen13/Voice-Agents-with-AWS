"""
Base Tool
Abstract base class for all restaurant tools
"""
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Dict


class BaseTool(ABC):
    """Base class for all restaurant tools with common patterns"""

    def __init__(self, dynamodb):
        """
        Initialize base tool with DynamoDB resource

        Args:
            dynamodb: boto3 DynamoDB resource
        """
        self.dynamodb = dynamodb

    def convert_decimals(self, obj: Any) -> Any:
        """
        Recursively convert Decimal objects to strings for JSON serialization

        Args:
            obj: Object to convert (can be dict, list, Decimal, or primitive)

        Returns:
            Object with all Decimals converted to strings
        """
        if isinstance(obj, list):
            return [self.convert_decimals(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: self.convert_decimals(value) for key, value in obj.items()}
        elif isinstance(obj, Decimal):
            return str(obj)
        else:
            return obj

    @abstractmethod
    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute tool logic - must be implemented by subclasses

        Args:
            content_data: Dictionary containing tool parameters

        Returns:
            Dictionary containing tool execution results
        """
        raise NotImplementedError("Subclasses must implement execute()")
