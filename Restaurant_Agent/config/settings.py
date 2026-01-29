"""
Settings Module
Environment-based configuration for the restaurant agent
"""
import os
from dataclasses import dataclass
from typing import Optional
from config.constants import *


@dataclass
class RestaurantConfig:
    """Restaurant Agent Configuration"""
    
    # AWS Configuration
    aws_region: str = DEFAULT_AWS_REGION
    aws_access_key: Optional[str] = None
    aws_secret_key: Optional[str] = None
    
    # DynamoDB Tables
    reservations_table: str = TABLE_RESERVATIONS
    waitlist_table: str = TABLE_WAITLIST
    tables_table: str = TABLE_TABLES
    customers_table: str = TABLE_CUSTOMERS
    orders_table: str = TABLE_ORDERS
    menu_table: str = TABLE_MENU
    notifications_table: str = TABLE_NOTIFICATIONS
    
    # Bedrock Model Configuration
    model_max_tokens: int = MODEL_MAX_TOKENS
    model_top_p: float = MODEL_TOP_P
    model_temperature: float = MODEL_TEMPERATURE
    
    # Debug Mode
    debug_mode: bool = False

    @classmethod
    def from_env(cls) -> 'RestaurantConfig':
        """Load configuration from environment variables"""
        return cls(
            aws_region=os.getenv("AWS_REGION", DEFAULT_AWS_REGION),
            aws_access_key=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            reservations_table=os.getenv("RESTAURANT_RESERVATIONS_TABLE", TABLE_RESERVATIONS),
            waitlist_table=os.getenv("RESTAURANT_WAITLIST_TABLE", TABLE_WAITLIST),
            tables_table=os.getenv("RESTAURANT_TABLES_TABLE", TABLE_TABLES),
            customers_table=os.getenv("RESTAURANT_CUSTOMERS_TABLE", TABLE_CUSTOMERS),
            orders_table=os.getenv("RESTAURANT_ORDERS_TABLE", TABLE_ORDERS),
            menu_table=os.getenv("RESTAURANT_MENU_TABLE", TABLE_MENU),
            notifications_table=os.getenv("RESTAURANT_NOTIFICATIONS_TABLE", TABLE_NOTIFICATIONS),
            debug_mode=os.getenv("DEBUG", "false").lower() == "true",
        )


# Global configuration instance
_config: Optional[RestaurantConfig] = None


def get_config() -> RestaurantConfig:
    """Get the global configuration instance (singleton pattern)"""
    global _config
    if _config is None:
        _config = RestaurantConfig.from_env()
    return _config
