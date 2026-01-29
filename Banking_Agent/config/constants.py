"""
Banking Agent Constants
All magic numbers and strings centralized here
"""

# Audio Configuration
INPUT_SAMPLE_RATE = 16000
OUTPUT_SAMPLE_RATE = 24000
CHANNELS = 1
CHUNK_SIZE = 1024

# Authentication Levels
AUTH_LEVEL_1 = "Level1"  # Phone verified
AUTH_LEVEL_2 = "Level2"  # Phone + OTP
AUTH_LEVEL_3 = "Level3"  # Phone + OTP + Knowledge

# Session Configuration
SESSION_TIMEOUT_MINUTES = 30
SESSION_ID_PREFIX = "SESSION"

# OTP Configuration
OTP_LENGTH = 6
OTP_MIN_VALUE = 100000
OTP_MAX_VALUE = 999999
OTP_EXPIRY_MINUTES = 5

# Audit Results
AUDIT_RESULT_SUCCESS = "SUCCESS"
AUDIT_RESULT_FAILURE = "FAILURE"

# ID Generation
RANDOM_SUFFIX_MIN = 100
RANDOM_SUFFIX_MAX = 999

# DynamoDB Table Names (defaults, can be overridden by config)
TABLE_CUSTOMERS = "Banking_Customers"
TABLE_ACCOUNTS = "Banking_Accounts"
TABLE_TRANSACTIONS = "Banking_Transactions"
TABLE_CARDS = "Banking_Cards"
TABLE_DISPUTES = "Banking_Disputes"
TABLE_TRANSFERS = "Banking_Transfers"
TABLE_AUTH_SESSIONS = "Banking_AuthSessions"
TABLE_AUDIT_LOGS = "Banking_AuditLogs"
TABLE_CONSENTS = "Banking_Consents"
TABLE_BILLPAY = "Banking_BillPay"

# AWS Configuration
DEFAULT_AWS_REGION = "us-east-1"
BEDROCK_MODEL_ID = "amazon.nova-sonic-v1:0"

# Audio Format
AUDIO_FORMAT_PCM_16 = "paInt16"

# Tool Names (normalized)
TOOL_AUTHENTICATE = "authenticatetool"
TOOL_VERIFY_OTP = "verifyotptool"
TOOL_STEP_UP_AUTH = "stepupauthenticationtool"
TOOL_CHECK_BALANCE = "checkbalancetool"
TOOL_VIEW_TRANSACTIONS = "viewrecenttransactionstool"
TOOL_SEARCH_TRANSACTIONS = "searchtransactionstool"
TOOL_REQUEST_STATEMENT = "requeststatementtool"
TOOL_REPORT_LOST_CARD = "reportlostcardtool"
TOOL_FREEZE_CARD = "freezecardtool"
TOOL_UNFREEZE_CARD = "unfreezecardtool"
TOOL_CHECK_REPLACEMENT = "checkreplacementstatustool"
TOOL_DISPUTE_CHARGE = "disputechargetool"
TOOL_CLARIFY_MERCHANT = "clarifymerchanttool"
TOOL_INTERNAL_TRANSFER = "internaltransfertool"
TOOL_CHECK_ZELLE = "checkzellestatustool"
TOOL_SETUP_BILLPAY = "setupbillpaytool"
TOOL_STOP_PAYMENT = "stoppaymenttool"
TOOL_EXPLAIN_PENDING = "explainpendingtool"
TOOL_REPORT_FRAUD = "reportfraudtool"
TOOL_CHECK_DISPUTE = "checkdisputestatustool"
TOOL_EXPLAIN_PROVISIONAL = "explainprovisionalcredittool"
