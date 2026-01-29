"""
Settings Module
Environment-based HIPAA-compliant configuration for the healthcare agent
"""
import os
from dataclasses import dataclass
from typing import Optional
from config.constants import *


@dataclass
class HealthcareConfig:
    """Healthcare Agent Configuration - HIPAA Compliant"""
    
    # AWS Configuration
    aws_region: str = DEFAULT_AWS_REGION
    aws_access_key: Optional[str] = None
    aws_secret_key: Optional[str] = None
    
    # DynamoDB Tables
    patients_table: str = TABLE_PATIENTS
    appointments_table: str = TABLE_APPOINTMENTS
    providers_table: str = TABLE_PROVIDERS
    locations_table: str = TABLE_LOCATIONS
    availability_table: str = TABLE_AVAILABILITY
    insurance_table: str = TABLE_INSURANCE
    referrals_table: str = TABLE_REFERRALS
    intake_forms_table: str = TABLE_INTAKE_FORMS
    audit_logs_table: str = TABLE_AUDIT_LOGS
    sessions_table: str = TABLE_SESSIONS
    
    # Bedrock Model Configuration
    model_max_tokens: int = MODEL_MAX_TOKENS
    model_top_p: float = MODEL_TOP_P
    model_temperature: float = MODEL_TEMPERATURE
    
    # HIPAA Compliance Settings
    session_timeout_minutes: int = SESSION_TIMEOUT_MINUTES
    session_warning_minutes: int = SESSION_WARNING_MINUTES
    max_verification_attempts: int = MAX_VERIFICATION_ATTEMPTS
    require_explicit_consent: bool = REQUIRE_EXPLICIT_CONSENT
    minimum_necessary_principle: bool = MINIMUM_NECESSARY_PRINCIPLE
    
    # Audit & Logging
    enable_audit_logging: bool = ENABLE_AUDIT_LOGGING
    log_all_phi_access: bool = LOG_ALL_PHI_ACCESS
    log_verification_attempts: bool = LOG_VERIFICATION_ATTEMPTS
    log_consent_capture: bool = LOG_CONSENT_CAPTURE
    
    # Slot Management
    slot_hold_minutes: int = SLOT_HOLD_MINUTES
    
    # Debug Mode (HIPAA: NEVER enable in production)
    debug_mode: bool = False
    
    # Encryption (HIPAA Required)
    encrypt_phi_at_rest: bool = True
    encrypt_phi_in_transit: bool = True

    @classmethod
    def from_env(cls) -> 'HealthcareConfig':
        """Load configuration from environment variables"""
        return cls(
            aws_region=os.getenv("AWS_REGION", DEFAULT_AWS_REGION),
            aws_access_key=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            patients_table=os.getenv("HEALTHCARE_PATIENTS_TABLE", TABLE_PATIENTS),
            appointments_table=os.getenv("HEALTHCARE_APPOINTMENTS_TABLE", TABLE_APPOINTMENTS),
            providers_table=os.getenv("HEALTHCARE_PROVIDERS_TABLE", TABLE_PROVIDERS),
            locations_table=os.getenv("HEALTHCARE_LOCATIONS_TABLE", TABLE_LOCATIONS),
            availability_table=os.getenv("HEALTHCARE_AVAILABILITY_TABLE", TABLE_AVAILABILITY),
            insurance_table=os.getenv("HEALTHCARE_INSURANCE_TABLE", TABLE_INSURANCE),
            referrals_table=os.getenv("HEALTHCARE_REFERRALS_TABLE", TABLE_REFERRALS),
            intake_forms_table=os.getenv("HEALTHCARE_INTAKE_FORMS_TABLE", TABLE_INTAKE_FORMS),
            audit_logs_table=os.getenv("HEALTHCARE_AUDIT_LOGS_TABLE", TABLE_AUDIT_LOGS),
            sessions_table=os.getenv("HEALTHCARE_SESSIONS_TABLE", TABLE_SESSIONS),
            debug_mode=os.getenv("DEBUG", "false").lower() == "true",
        )
    
    def validate_hipaa_compliance(self) -> bool:
        """Validate HIPAA compliance settings"""
        if self.debug_mode:
            raise ValueError("HIPAA VIOLATION: Debug mode cannot be enabled in production")
        
        if not self.enable_audit_logging:
            raise ValueError("HIPAA VIOLATION: Audit logging is required")
        
        if not self.encrypt_phi_at_rest:
            raise ValueError("HIPAA VIOLATION: PHI must be encrypted at rest")
        
        if not self.encrypt_phi_in_transit:
            raise ValueError("HIPAA VIOLATION: PHI must be encrypted in transit")
        
        return True


# Global configuration instance
_config: Optional[HealthcareConfig] = None


def get_config() -> HealthcareConfig:
    """Get the global configuration instance (singleton pattern)"""
    global _config
    if _config is None:
        _config = HealthcareConfig.from_env()
        # Validate HIPAA compliance on initialization
        _config.validate_hipaa_compliance()
    return _config
