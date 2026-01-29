"""
Retail Member Service Assistant - Refactored
Main entry point for the retail customer service voice agent

This is the refactored modular version using extracted components.
All business logic has been extracted into separate modules.
"""
import os
import asyncio
import boto3
import warnings
from config.settings import get_config
from core.retail_tool_processor import RetailToolProcessor
from streaming.bedrock_manager import BedrockStreamManager
from streaming.audio_streamer import AudioStreamer

# Suppress warnings
warnings.filterwarnings("ignore")


async def main(debug=False):
    """Main entry point for retail customer service agent"""

    # Get configuration and set debug mode
    config = get_config()
    config.debug_mode = debug

    print("\n" + "="*60)
    print("🛒 Retail Member Service Assistant - Voice Agent")
    print("="*60)
    print("\nInitializing connection to AWS Bedrock...")

    # Initialize DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name=config.aws_region)

    # Initialize tool processor
    tool_processor = RetailToolProcessor(dynamodb)

    # Initialize stream manager
    stream_manager = BedrockStreamManager(tool_processor)
    await stream_manager.initialize_stream()

    # Initialize audio streamer
    audio_streamer = AudioStreamer(stream_manager)
    await audio_streamer.start()

    # Run both stream processing and audio output concurrently
    try:
        await asyncio.gather(
            stream_manager.process_stream_events(),
            audio_streamer.play_output_audio(),
        )
    except KeyboardInterrupt:
        print("\n\nShutting down retail member service assistant...")
    finally:
        await audio_streamer.stop()


if __name__ == "__main__":
    # Note: AWS credentials should be set via environment variables
    # or AWS credentials file, not hard-coded in the script

    # Example of setting environment variables (remove or use proper config):
    # os.environ["AWS_ACCESS_KEY_ID"] = "your_aws_access_key_id"
    # os.environ["AWS_SECRET_ACCESS_KEY"] = "your_aws_secret_access_key"
    # os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

    import argparse
    parser = argparse.ArgumentParser(description="Retail Customer Service Voice Agent")
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    asyncio.run(main(debug=args.debug))
