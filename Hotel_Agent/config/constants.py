"""
Configuration Constants for Hotel Agent
All magic numbers and constant values centralized here
"""
import pyaudio

# Audio Configuration
INPUT_SAMPLE_RATE = 16000
OUTPUT_SAMPLE_RATE = 24000
CHANNELS = 1
AUDIO_FORMAT = pyaudio.paInt16
CHUNK_SIZE = 1024

# AWS Configuration
DEFAULT_AWS_REGION = "us-east-1"

# DynamoDB Table Names
TABLE_GUESTS = "Hotel_Guests"
TABLE_RESERVATIONS = "Hotel_Reservations"

# Bedrock Model Configuration
MODEL_MAX_TOKENS = 1024
MODEL_TOP_P = 0.9
MODEL_TEMPERATURE = 0.7

# Tool Names (normalized - lowercase, no spaces)
TOOL_CHECK_GUEST_PROFILE = "checkguestprofiletool"
TOOL_CHECK_RESERVATION_STATUS = "checkreservationstatustool"
TOOL_UPDATE_RESERVATION = "updatereservationtool"

# Date Format
DATE_FORMAT = "%Y-%m-%d"
