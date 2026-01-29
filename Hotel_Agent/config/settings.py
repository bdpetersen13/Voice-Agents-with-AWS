"""
Configuration Settings for Hotel Agent
Supports environment variables and provides configuration management
"""
import os
from dataclasses import dataclass
from typing import Optional
from config.constants import *


@dataclass
class HotelConfig:
    """Hotel Agent Configuration"""

    # AWS Configuration
    aws_region: str = DEFAULT_AWS_REGION
    aws_access_key: Optional[str] = None
    aws_secret_key: Optional[str] = None

    # DynamoDB Tables
    guests_table: str = TABLE_GUESTS
    reservations_table: str = TABLE_RESERVATIONS

    # Bedrock Model Settings
    model_max_tokens: int = MODEL_MAX_TOKENS
    model_top_p: float = MODEL_TOP_P
    model_temperature: float = MODEL_TEMPERATURE

    # Audio Settings
    input_sample_rate: int = INPUT_SAMPLE_RATE
    output_sample_rate: int = OUTPUT_SAMPLE_RATE
    channels: int = CHANNELS
    chunk_size: int = CHUNK_SIZE

    # Debug Mode
    debug_mode: bool = False

    @classmethod
    def from_env(cls) -> 'HotelConfig':
        """Load configuration from environment variables"""
        return cls(
            aws_region=os.getenv("AWS_REGION", DEFAULT_AWS_REGION),
            aws_access_key=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            guests_table=os.getenv("HOTEL_GUESTS_TABLE", TABLE_GUESTS),
            reservations_table=os.getenv("HOTEL_RESERVATIONS_TABLE", TABLE_RESERVATIONS),
            debug_mode=os.getenv("DEBUG", "false").lower() == "true"
        )


# Global configuration instance
_config: Optional[HotelConfig] = None


def get_config() -> HotelConfig:
    """Get or create global configuration instance"""
    global _config
    if _config is None:
        _config = HotelConfig.from_env()
    return _config


def set_config(config: HotelConfig):
    """Set global configuration instance"""
    global _config
    _config = config
