"""
Constants Module
All magic numbers and constant values for the call center agent
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
TABLE_MEMBERS = "CallCenter_Members"
TABLE_STORE_INFO = "CallCenter_Store_Info"
TABLE_INVENTORY = "CallCenter_Inventory"
TABLE_CURBSIDE_ORDERS = "CallCenter_Curbside_Orders"
TABLE_APPOINTMENTS = "CallCenter_Appointments"
TABLE_SPECIALTY_ORDERS = "CallCenter_Specialty_Orders"
TABLE_CAKE_ORDERS = "CallCenter_Cake_Orders"

# Bedrock Model Configuration
MODEL_MAX_TOKENS = 1024
MODEL_TOP_P = 0.9
MODEL_TEMPERATURE = 0.7

# Tool Names (normalized for lookup)
TOOL_VERIFY_MEMBER = "verifymember"
TOOL_CHECK_STORE_HOURS = "checkstorehours"
TOOL_CHECK_INVENTORY = "checkinventory"
TOOL_CHECK_CURBSIDE_ORDER = "checkcurbsideorder"
TOOL_SCHEDULE_APPOINTMENT = "scheduleappointment"
TOOL_CHECK_SPECIALTY_ORDER = "checkspecialtyorder"
TOOL_CREATE_CAKE_ORDER = "createcakeorder"
TOOL_CHECK_APPOINTMENT = "checkappointment"
