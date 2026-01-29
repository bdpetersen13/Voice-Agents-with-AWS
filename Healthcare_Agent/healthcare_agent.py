"""
Healthcare Appointment Scheduling Assistant - HIPAA Compliant
Main entry point for the healthcare voice agent

This agent provides HIPAA-compliant appointment scheduling with:
- Identity verification and consent capture
- Session timeout (15 minutes)
- Full PHI access audit logging
- 20 specialized healthcare tools
- Escalation for medical details (never discusses medical information)
"""
import os
import asyncio
import boto3
import warnings
import uuid

from config.settings import get_config
from security.session_manager import SessionManager
from security.audit_logger import AuditLogger
from core.tool_processor import ToolProcessor
from streaming.bedrock_manager import BedrockStreamManager
from streaming.audio_streamer import AudioStreamer
from utils.logging import log_info, log_error

# Suppress warnings
warnings.filterwarnings("ignore")


async def main(debug=False):
    """Main entry point for healthcare appointment scheduling agent"""

    # Get configuration and validate HIPAA compliance
    config = get_config()
    config.debug_mode = debug

    # Validate HIPAA compliance (will raise exception if invalid)
    try:
        config.validate_hipaa_compliance()
    except ValueError as e:
        log_error(f"HIPAA compliance validation failed: {e}")
        print(f"\n❌ HIPAA COMPLIANCE ERROR: {e}")
        print("Please fix the configuration and try again.\n")
        return

    print("\n" + "="*60)
    print("🏥 Healthcare Appointment Scheduling Assistant")
    print("="*60)
    print("HIPAA-Compliant Voice Agent")
    print("- Identity verification required")
    print("- Session timeout: 15 minutes")
    print("- Full audit logging enabled")
    print("- Medical details escalated to clinical staff")
    print("="*60)
    print("\nInitializing secure connection to AWS Bedrock...")

    # Initialize DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name=config.aws_region)

    # Initialize HIPAA security components
    log_info("Initializing HIPAA security components")

    audit_logger = AuditLogger(
        dynamodb=dynamodb,
        audit_logs_table=dynamodb.Table(config.table_audit_logs)
    )

    session_manager = SessionManager(
        dynamodb=dynamodb,
        sessions_table=dynamodb.Table(config.table_sessions),
        audit_logger=audit_logger
    )

    # Create session for this conversation
    session = session_manager.create_session()
    session_id = session['sessionId']
    log_info(f"Created session: {session_id}")
    print(f"\n✓ Session created: {session_id}")
    print(f"✓ Session expires at: {session['expiresAt']}")

    # Initialize tool processor with all 20 healthcare tools
    log_info("Initializing healthcare tool processor with 20 tools")
    tool_processor = ToolProcessor(
        dynamodb=dynamodb,
        config=config,
        session_manager=session_manager,
        audit_logger=audit_logger
    )

    print(f"✓ Loaded {tool_processor.get_tool_count()} healthcare tools")

    # Initialize stream manager
    log_info("Initializing Bedrock stream manager")
    stream_manager = BedrockStreamManager(
        tool_processor=tool_processor,
        model_id=config.model_id,
        region=config.aws_region
    )
    await stream_manager.initialize_stream()
    print("✓ Bedrock stream initialized")

    # Initialize audio streamer
    log_info("Initializing audio streamer")
    audio_streamer = AudioStreamer(stream_manager)
    await audio_streamer.start()
    print("✓ Audio streamer started")

    print("\n" + "="*60)
    print("🎤 Ready to assist with appointment scheduling")
    print("="*60)
    print("\nIMPORTANT REMINDERS:")
    print("- This agent schedules appointments ONLY")
    print("- Medical questions will be escalated to clinical staff")
    print("- Identity verification required before scheduling")
    print("- Session will timeout after 15 minutes of inactivity")
    print("\nPress Ctrl+C to exit\n")

    # Session timeout monitoring
    async def monitor_session_timeout():
        """Monitor session timeout and warn user"""
        while True:
            await asyncio.sleep(30)  # Check every 30 seconds

            session_data = session_manager.get_session(session_id)
            if not session_data:
                log_info("Session expired")
                print("\n⚠️  Session has expired for security. Please restart to continue.")
                # Could trigger graceful shutdown here
                break

            # Check if warning should be displayed
            if session_manager.check_warning(session_id):
                print("\n⚠️  SESSION WARNING: Your session will expire in 2 minutes due to inactivity.")
                print("    Continue the conversation to extend your session.\n")

    # Run all tasks concurrently
    try:
        await asyncio.gather(
            audio_streamer.play_output_audio(),
            monitor_session_timeout(),
        )
    except KeyboardInterrupt:
        print("\n\nShutting down healthcare appointment assistant...")
    finally:
        # Clean up
        log_info("Cleaning up and terminating session")
        await audio_streamer.stop()
        await stream_manager.close()

        # Terminate session with audit log
        session_manager.terminate_session(session_id)
        print("\n✓ Session terminated securely")
        print("✓ All PHI access has been logged")
        print("\nThank you for using the Healthcare Appointment Scheduling Assistant.\n")


if __name__ == "__main__":
    """
    Entry point for healthcare appointment scheduling agent

    IMPORTANT: AWS credentials should be set via environment variables
    or AWS credentials file, not hard-coded in the script.

    Required environment variables:
    - AWS_ACCESS_KEY_ID
    - AWS_SECRET_ACCESS_KEY
    - AWS_DEFAULT_REGION (default: us-east-1)

    Optional environment variables:
    - HEALTHCARE_DEBUG_MODE (true/false)
    - HEALTHCARE_MODEL_ID (default: amazon.nova-sonic-v1:0)

    HIPAA Compliance Requirements:
    - Audit logging must be enabled (always on)
    - Debug mode should be disabled in production
    - Encryption at rest and in transit required
    - Session timeout: 15 minutes

    Usage:
        python healthcare_agent.py              # Normal mode
        python healthcare_agent.py --debug      # Debug mode (NOT for production)
    """

    import argparse

    parser = argparse.ArgumentParser(
        description="HIPAA-Compliant Healthcare Appointment Scheduling Voice Agent"
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode (WARNING: Do not use in production - HIPAA violation)'
    )

    args = parser.parse_args()

    # Warn about debug mode
    if args.debug:
        print("\n" + "="*60)
        print("⚠️  WARNING: DEBUG MODE ENABLED")
        print("="*60)
        print("Debug mode should NEVER be used in production environments.")
        print("This may violate HIPAA compliance by exposing PHI in logs.")
        print("Use only in development/testing environments.")
        print("="*60 + "\n")

        response = input("Are you sure you want to continue in debug mode? (yes/no): ")
        if response.lower() != "yes":
            print("Exiting...")
            exit(0)

    asyncio.run(main(debug=args.debug))
