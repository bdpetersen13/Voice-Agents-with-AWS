"""
Settings Module
Environment-based configuration for the call center agent
"""
import os
from dataclasses import dataclass
from typing import Optional
from config.constants import (
    DEFAULT_AWS_REGION,
    TABLE_MEMBERS,
    TABLE_STORE_INFO,
    TABLE_INVENTORY,
    TABLE_CURBSIDE_ORDERS,
    TABLE_APPOINTMENTS,
    TABLE_SPECIALTY_ORDERS,
    TABLE_CAKE_ORDERS,
    MODEL_MAX_TOKENS,
    MODEL_TOP_P,
    MODEL_TEMPERATURE,
)


@dataclass
class CallCenterConfig:
    """Call Center Agent Configuration"""
    
    # AWS Configuration
    aws_region: str = DEFAULT_AWS_REGION
    aws_access_key: Optional[str] = None
    aws_secret_key: Optional[str] = None
    
    # DynamoDB Tables
    members_table: str = TABLE_MEMBERS
    store_info_table: str = TABLE_STORE_INFO
    inventory_table: str = TABLE_INVENTORY
    curbside_orders_table: str = TABLE_CURBSIDE_ORDERS
    appointments_table: str = TABLE_APPOINTMENTS
    specialty_orders_table: str = TABLE_SPECIALTY_ORDERS
    cake_orders_table: str = TABLE_CAKE_ORDERS
    
    # Bedrock Model Configuration
    model_max_tokens: int = MODEL_MAX_TOKENS
    model_top_p: float = MODEL_TOP_P
    model_temperature: float = MODEL_TEMPERATURE
    
    # Debug Mode
    debug_mode: bool = False

    @classmethod
    def from_env(cls) -> 'CallCenterConfig':
        """Load configuration from environment variables"""
        return cls(
            aws_region=os.getenv("AWS_REGION", DEFAULT_AWS_REGION),
            aws_access_key=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            members_table=os.getenv("CALLCENTER_MEMBERS_TABLE", TABLE_MEMBERS),
            store_info_table=os.getenv("CALLCENTER_STORE_INFO_TABLE", TABLE_STORE_INFO),
            inventory_table=os.getenv("CALLCENTER_INVENTORY_TABLE", TABLE_INVENTORY),
            curbside_orders_table=os.getenv("CALLCENTER_CURBSIDE_ORDERS_TABLE", TABLE_CURBSIDE_ORDERS),
            appointments_table=os.getenv("CALLCENTER_APPOINTMENTS_TABLE", TABLE_APPOINTMENTS),
            specialty_orders_table=os.getenv("CALLCENTER_SPECIALTY_ORDERS_TABLE", TABLE_SPECIALTY_ORDERS),
            cake_orders_table=os.getenv("CALLCENTER_CAKE_ORDERS_TABLE", TABLE_CAKE_ORDERS),
            debug_mode=os.getenv("DEBUG", "false").lower() == "true",
        )


# Global configuration instance
_config: Optional[CallCenterConfig] = None


def get_config() -> CallCenterConfig:
    """Get the global configuration instance (singleton pattern)"""
    global _config
    if _config is None:
        _config = CallCenterConfig.from_env()
    return _config
