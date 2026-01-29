"""
Banking Agent Settings
Configuration management with environment variable support
"""
import os
from typing import Optional
from dataclasses import dataclass
import pyaudio
from config.constants import *


@dataclass
class BankingConfig:
    """Banking Agent Configuration"""

    # AWS Configuration
    aws_region: str = DEFAULT_AWS_REGION
    aws_access_key: Optional[str] = None
    aws_secret_key: Optional[str] = None

    # DynamoDB Table Names
    customers_table: str = TABLE_CUSTOMERS
    accounts_table: str = TABLE_ACCOUNTS
    transactions_table: str = TABLE_TRANSACTIONS
    cards_table: str = TABLE_CARDS
    disputes_table: str = TABLE_DISPUTES
    transfers_table: str = TABLE_TRANSFERS
    auth_sessions_table: str = TABLE_AUTH_SESSIONS
    audit_logs_table: str = TABLE_AUDIT_LOGS
    consents_table: str = TABLE_CONSENTS
    billpay_table: str = TABLE_BILLPAY

    # Audio Configuration
    input_sample_rate: int = INPUT_SAMPLE_RATE
    output_sample_rate: int = OUTPUT_SAMPLE_RATE
    channels: int = CHANNELS
    audio_format: int = pyaudio.paInt16
    chunk_size: int = CHUNK_SIZE

    # Security Configuration
    session_timeout_minutes: int = SESSION_TIMEOUT_MINUTES
    otp_expiry_minutes: int = OTP_EXPIRY_MINUTES
    otp_length: int = OTP_LENGTH

    # Bedrock Configuration
    bedrock_model_id: str = BEDROCK_MODEL_ID

    # Debug Mode
    debug_mode: bool = False

    @classmethod
    def from_env(cls) -> 'BankingConfig':
        """Load configuration from environment variables"""
        return cls(
            # AWS
            aws_region=os.getenv("AWS_REGION", DEFAULT_AWS_REGION),
            aws_access_key=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_key=os.getenv("AWS_SECRET_ACCESS_KEY"),

            # Tables (allow override via env vars)
            customers_table=os.getenv("CUSTOMERS_TABLE", TABLE_CUSTOMERS),
            accounts_table=os.getenv("ACCOUNTS_TABLE", TABLE_ACCOUNTS),
            transactions_table=os.getenv("TRANSACTIONS_TABLE", TABLE_TRANSACTIONS),
            cards_table=os.getenv("CARDS_TABLE", TABLE_CARDS),
            disputes_table=os.getenv("DISPUTES_TABLE", TABLE_DISPUTES),
            transfers_table=os.getenv("TRANSFERS_TABLE", TABLE_TRANSFERS),
            auth_sessions_table=os.getenv("AUTH_SESSIONS_TABLE", TABLE_AUTH_SESSIONS),
            audit_logs_table=os.getenv("AUDIT_LOGS_TABLE", TABLE_AUDIT_LOGS),
            consents_table=os.getenv("CONSENTS_TABLE", TABLE_CONSENTS),
            billpay_table=os.getenv("BILLPAY_TABLE", TABLE_BILLPAY),

            # Audio
            input_sample_rate=int(os.getenv("INPUT_SAMPLE_RATE", INPUT_SAMPLE_RATE)),
            output_sample_rate=int(os.getenv("OUTPUT_SAMPLE_RATE", OUTPUT_SAMPLE_RATE)),

            # Security
            session_timeout_minutes=int(os.getenv("SESSION_TIMEOUT_MINUTES", SESSION_TIMEOUT_MINUTES)),
            otp_expiry_minutes=int(os.getenv("OTP_EXPIRY_MINUTES", OTP_EXPIRY_MINUTES)),

            # Debug
            debug_mode=os.getenv("DEBUG", "false").lower() == "true"
        )


# Global config instance
_config: Optional[BankingConfig] = None


def get_config() -> BankingConfig:
    """Get or create global configuration instance"""
    global _config
    if _config is None:
        _config = BankingConfig.from_env()
    return _config


def set_config(config: BankingConfig):
    """Set global configuration instance"""
    global _config
    _config = config
