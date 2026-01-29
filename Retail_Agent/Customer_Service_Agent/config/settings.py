"""
Settings Module
Environment-based configuration for the retail customer service agent
"""
import os
from dataclasses import dataclass
from typing import Optional
from config.constants import (
    DEFAULT_AWS_REGION,
    TABLE_MEMBERS,
    TABLE_TRANSACTIONS,
    TABLE_RETURNS,
    TABLE_SERVICE_REQUESTS,
    MODEL_MAX_TOKENS,
    MODEL_TOP_P,
    MODEL_TEMPERATURE,
)


@dataclass
class RetailConfig:
    """Retail Customer Service Agent Configuration"""
    
    # AWS Configuration
    aws_region: str = DEFAULT_AWS_REGION
    aws_access_key: Optional[str] = None
    aws_secret_key: Optional[str] = None
    
    # DynamoDB Tables
    members_table: str = TABLE_MEMBERS
    transactions_table: str = TABLE_TRANSACTIONS
    returns_table: str = TABLE_RETURNS
    service_requests_table: str = TABLE_SERVICE_REQUESTS
    
    # Bedrock Model Configuration
    model_max_tokens: int = MODEL_MAX_TOKENS
    model_top_p: float = MODEL_TOP_P
    model_temperature: float = MODEL_TEMPERATURE
    
    # Debug Mode
    debug_mode: bool = False

    @classmethod
    def from_env(cls) -> 'RetailConfig':
        """Load configuration from environment variables"""
        return cls(
            aws_region=os.getenv("AWS_REGION", DEFAULT_AWS_REGION),
            aws_access_key=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            members_table=os.getenv("RETAIL_MEMBERS_TABLE", TABLE_MEMBERS),
            transactions_table=os.getenv("RETAIL_TRANSACTIONS_TABLE", TABLE_TRANSACTIONS),
            returns_table=os.getenv("RETAIL_RETURNS_TABLE", TABLE_RETURNS),
            service_requests_table=os.getenv("RETAIL_SERVICE_REQUESTS_TABLE", TABLE_SERVICE_REQUESTS),
            debug_mode=os.getenv("DEBUG", "false").lower() == "true",
        )


# Global configuration instance
_config: Optional[RetailConfig] = None


def get_config() -> RetailConfig:
    """Get the global configuration instance (singleton pattern)"""
    global _config
    if _config is None:
        _config = RetailConfig.from_env()
    return _config
