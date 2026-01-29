"""
Constants Module
All magic numbers and constant values for the restaurant agent
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
TABLE_RESERVATIONS = "Restaurant_Reservations"
TABLE_WAITLIST = "Restaurant_Waitlist"
TABLE_TABLES = "Restaurant_Tables"
TABLE_CUSTOMERS = "Restaurant_Customers"
TABLE_ORDERS = "Restaurant_Orders"
TABLE_MENU = "Restaurant_Menu"
TABLE_NOTIFICATIONS = "Restaurant_Notifications"

# Bedrock Model Configuration
MODEL_ID = "amazon.nova-sonic-v1:0"
MODEL_MAX_TOKENS = 1024
MODEL_TOP_P = 0.9
MODEL_TEMPERATURE = 0.7

# Tool Names (normalized for lookup)
TOOL_LOOKUP_RESERVATION = "lookupreservationtool"
TOOL_CREATE_RESERVATION = "createreservationtool"
TOOL_EDIT_RESERVATION = "editreservationtool"
TOOL_CANCEL_RESERVATION = "cancelreservationtool"
TOOL_CONFIRM_RESERVATION = "confirmreservationtool"
TOOL_JOIN_WAITLIST = "joinwaitlisttool"
TOOL_CHECK_WAIT_TIME = "checkwaittimetool"
TOOL_NOTIFY_TABLE_READY = "notifytablereadytool"
TOOL_SEAT_GUEST = "seatguesttool"
TOOL_PLACE_ORDER = "placeordertool"
TOOL_VIEW_MENU = "viewmenutool"
TOOL_CHECK_ORDER_STATUS = "checkorderstatus tool"

# Wait Time Configuration
WAIT_TIME_SMALL_PARTY = (15, 30)  # party size <= 2
WAIT_TIME_MEDIUM_PARTY = (25, 45)  # party size <= 4
WAIT_TIME_LARGE_PARTY = (35, 60)  # party size <= 6
WAIT_TIME_XLARGE_PARTY = (45, 90)  # party size > 6

# Table Capacity Buffer
TABLE_CAPACITY_BUFFER = 2  # Allow tables up to party_size + 2

# Tax Rate
TAX_RATE = 0.08  # 8%

# Reservation ID Prefixes
RESERVATION_ID_PREFIX = "RES"
WAITLIST_ID_PREFIX = "WAIT"
ORDER_ID_PREFIX = "ORD"
NOTIFICATION_ID_PREFIX = "NOTIF"
