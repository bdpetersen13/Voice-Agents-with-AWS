"""
First National Bank - Secure Voice Banking Agent
Refactored modular version using extracted components

This is the main entry point for the banking voice agent.
All business logic has been extracted into separate modules.
"""
import os
import asyncio
import boto3
import warnings
from config.settings import get_config
from core.authentication import BankingAuthenticationManager
from core.tool_processor import BankingToolProcessor
from streaming.bedrock_manager import BedrockStreamManager
from streaming.audio_streamer import AudioStreamer

# Suppress warnings
warnings.filterwarnings("ignore")


async def main():
    """Main entry point for banking agent"""
    import argparse

    parser = argparse.ArgumentParser(description="Banking Voice Agent")
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    # Get configuration and set debug mode
    config = get_config()
    config.debug_mode = args.debug

    print("\n" + "="*60)
    print("🏦 First National Bank - Secure Voice Banking Agent")
    print("="*60)
    print("\nInitializing secure connection...")

    # Initialize DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name=config.aws_region)

    # Initialize authentication manager
    auth_manager = BankingAuthenticationManager(dynamodb)

    # Initialize tool processor
    tool_processor = BankingToolProcessor(dynamodb, auth_manager)

    # Initialize stream manager
    stream_manager = BedrockStreamManager(tool_processor)
    stream_manager.initialize_stream()

    # Send initial prompts
    await stream_manager.send_content_start()
    await stream_manager.send_content_end()

    # Initialize audio streamer
    audio_streamer = AudioStreamer(stream_manager)
    audio_streamer.start()

    # Run both stream processing and audio output concurrently
    try:
        await asyncio.gather(
            stream_manager.process_stream_events(),
            audio_streamer.play_output(),
        )
    except KeyboardInterrupt:
        print("\n\nShutting down banking agent...")
    finally:
        audio_streamer.stop()


if __name__ == "__main__":
    # Note: AWS credentials should be set via environment variables
    # or AWS credentials file, not hard-coded in the script

    # Example of setting environment variables (remove or use proper config):
    # os.environ["AWS_ACCESS_KEY_ID"] = "your_aws_access_key_id"
    # os.environ["AWS_SECRET_ACCESS_KEY"] = "your_aws_secret_access_key"
    # os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

    asyncio.run(main())
