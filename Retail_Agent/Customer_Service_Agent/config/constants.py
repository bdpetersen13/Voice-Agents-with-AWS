"""
Constants Module
All magic numbers and constant values for the retail customer service agent
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
TABLE_MEMBERS = "Retail_Members"
TABLE_TRANSACTIONS = "Retail_Transactions"
TABLE_RETURNS = "Retail_Returns"
TABLE_SERVICE_REQUESTS = "Retail_Service_Requests"

# Bedrock Model Configuration
MODEL_MAX_TOKENS = 1024
MODEL_TOP_P = 0.9
MODEL_TEMPERATURE = 0.7

# Tool Names (normalized for lookup)
TOOL_VERIFY_MEMBER = "verifymember"
TOOL_LOOKUP_TRANSACTION = "lookuptransaction"
TOOL_MODIFY_MEMBERSHIP = "modifymembership"
TOOL_ADD_HOUSEHOLD_MEMBER = "addhouseholdmember"
TOOL_REMOVE_HOUSEHOLD_MEMBER = "removehouseholdmember"
TOOL_VERIFY_RETURN_ITEM = "verifyreturnitem"
TOOL_INITIATE_RETURN = "initiatereturn"
TOOL_PROCESS_TRANSACTION_ISSUE = "processtransactionissue"
TOOL_FILE_COMPLAINT = "filecomplaint"
