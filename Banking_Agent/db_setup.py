import boto3
import datetime
import time
import random
import hashlib
from decimal import Decimal

def setup_banking_demo_data():
    """
    Sets up DynamoDB tables for a banking customer service agent.
    Creates tables for: Customers, Accounts, Transactions, Cards, Disputes, Transfers,
                       AuthSessions, AuditLogs, Consents, BillPay

    SECURITY FOCUSED: Multi-factor auth, audit trails, compliance tracking
    """
    # Initialize DynamoDB resource
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

    # --- 1. Define Table Schemas ---
    tables = {
        'Banking_Customers': {
            'KeySchema': [{'AttributeName': 'customerId', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'customerId', 'AttributeType': 'S'}]
        },
        'Banking_Accounts': {
            'KeySchema': [{'AttributeName': 'accountId', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'accountId', 'AttributeType': 'S'}]
        },
        'Banking_Transactions': {
            'KeySchema': [{'AttributeName': 'transactionId', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'transactionId', 'AttributeType': 'S'}]
        },
        'Banking_Cards': {
            'KeySchema': [{'AttributeName': 'cardId', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'cardId', 'AttributeType': 'S'}]
        },
        'Banking_Disputes': {
            'KeySchema': [{'AttributeName': 'disputeId', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'disputeId', 'AttributeType': 'S'}]
        },
        'Banking_Transfers': {
            'KeySchema': [{'AttributeName': 'transferId', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'transferId', 'AttributeType': 'S'}]
        },
        'Banking_AuthSessions': {
            'KeySchema': [{'AttributeName': 'sessionId', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'sessionId', 'AttributeType': 'S'}]
        },
        'Banking_AuditLogs': {
            'KeySchema': [{'AttributeName': 'auditId', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'auditId', 'AttributeType': 'S'}]
        },
        'Banking_Consents': {
            'KeySchema': [{'AttributeName': 'consentId', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'consentId', 'AttributeType': 'S'}]
        },
        'Banking_BillPay': {
            'KeySchema': [{'AttributeName': 'payeeId', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'payeeId', 'AttributeType': 'S'}]
        }
    }

    # --- 2. Delete Old Tables & Create New Ones ---
    print("--- Resetting Banking Database ---")
    for table_name, schema in tables.items():
        table = dynamodb.Table(table_name)

        # Delete if exists
        try:
            print(f"Deleting old table: {table_name}...")
            table.delete()
            table.wait_until_not_exists()
            print(f"Deleted {table_name}.")
        except Exception as e:
            if "ResourceNotFoundException" in str(e):
                pass
            else:
                print(f"Warning deleting {table_name}: {e}")

        # Create new
        print(f"Creating new table: {table_name}...")
        try:
            dynamodb.create_table(
                TableName=table_name,
                KeySchema=schema['KeySchema'],
                AttributeDefinitions=schema['AttributeDefinitions'],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )
            table = dynamodb.Table(table_name)
            table.wait_until_exists()
            print(f"Ready: {table_name}")
        except Exception as e:
            print(f"Error creating {table_name}: {e}")
            return

    # --- 3. Seed Customers ---
    print("\n--- Seeding Customers ---")
    customers = dynamodb.Table('Banking_Customers')

    customer_data = [
        {
            'customerId': 'CUST-10001',
            'name': 'Jennifer Martinez',
            'phone': '+1-555-234-5678',
            'email': 'jennifer.martinez@email.com',
            'dateOfBirth': '1985-03-15',
            'ssn_last4': '4521',  # Last 4 of SSN for verification
            'address': {
                'street': '123 Oak Street',
                'city': 'Denver',
                'state': 'CO',
                'zip': '80202'
            },
            'securityQuestions': {
                'mothersMaidenName': hashlib.sha256('Johnson'.encode()).hexdigest(),  # Hashed
                'firstPetName': hashlib.sha256('Max'.encode()).hexdigest()
            },
            'mfaEnabled': True,
            'mfaMethod': 'SMS',  # SMS, App, or Both
            'accountStatus': 'Active',
            'riskLevel': 'Low',  # Low, Medium, High (affects auth requirements)
            'jurisdiction': 'US-CO',  # For compliance
            'kycVerified': True,
            'createdAt': '2020-01-15T10:00:00Z'
        },
        {
            'customerId': 'CUST-10002',
            'name': 'Robert Chen',
            'phone': '+1-555-345-6789',
            'email': 'robert.chen@email.com',
            'dateOfBirth': '1978-11-22',
            'ssn_last4': '8832',
            'address': {
                'street': '456 Pine Avenue',
                'city': 'Denver',
                'state': 'CO',
                'zip': '80203'
            },
            'securityQuestions': {
                'mothersMaidenName': hashlib.sha256('Wong'.encode()).hexdigest(),
                'firstPetName': hashlib.sha256('Buddy'.encode()).hexdigest()
            },
            'mfaEnabled': True,
            'mfaMethod': 'Both',
            'accountStatus': 'Active',
            'riskLevel': 'Low',
            'jurisdiction': 'US-CO',
            'kycVerified': True,
            'createdAt': '2018-06-20T14:30:00Z'
        },
        {
            'customerId': 'CUST-10003',
            'name': 'Sarah Thompson',
            'phone': '+1-555-456-7890',
            'email': 'sarah.thompson@email.com',
            'dateOfBirth': '1992-07-08',
            'ssn_last4': '1156',
            'address': {
                'street': '789 Maple Lane',
                'city': 'Aurora',
                'state': 'CO',
                'zip': '80010'
            },
            'securityQuestions': {
                'mothersMaidenName': hashlib.sha256('Davis'.encode()).hexdigest(),
                'firstPetName': hashlib.sha256('Luna'.encode()).hexdigest()
            },
            'mfaEnabled': False,  # Not enrolled in MFA
            'mfaMethod': None,
            'accountStatus': 'Active',
            'riskLevel': 'Medium',  # Higher risk = more auth required
            'jurisdiction': 'US-CO',
            'kycVerified': True,
            'createdAt': '2021-03-10T09:15:00Z'
        }
    ]

    for customer in customer_data:
        customers.put_item(Item=customer)

    print(f"Customers seeded: {len(customer_data)} customers")

    # --- 4. Seed Accounts ---
    print("\n--- Seeding Accounts ---")
    accounts = dynamodb.Table('Banking_Accounts')

    account_data = [
        # Jennifer's accounts
        {
            'accountId': 'ACC-CHK-001',
            'customerId': 'CUST-10001',
            'accountType': 'Checking',
            'accountNumber': '****1234',  # Masked
            'accountNumberFull': '4532123456781234',  # Full (encrypted in production)
            'routingNumber': '102000076',
            'balance': Decimal('5847.32'),
            'availableBalance': Decimal('5647.32'),  # After pending holds
            'pendingTransactions': Decimal('200.00'),
            'currency': 'USD',
            'status': 'Active',
            'openedDate': '2020-01-15',
            'interestRate': Decimal('0.01'),
            'minimumBalance': Decimal('25.00')
        },
        {
            'accountId': 'ACC-SAV-001',
            'customerId': 'CUST-10001',
            'accountType': 'Savings',
            'accountNumber': '****5678',
            'accountNumberFull': '4532567812345678',
            'routingNumber': '102000076',
            'balance': Decimal('15320.50'),
            'availableBalance': Decimal('15320.50'),
            'pendingTransactions': Decimal('0.00'),
            'currency': 'USD',
            'status': 'Active',
            'openedDate': '2020-01-15',
            'interestRate': Decimal('0.45'),
            'minimumBalance': Decimal('500.00')
        },
        # Robert's accounts
        {
            'accountId': 'ACC-CHK-002',
            'customerId': 'CUST-10002',
            'accountType': 'Checking',
            'accountNumber': '****9012',
            'accountNumberFull': '4532901234569012',
            'routingNumber': '102000076',
            'balance': Decimal('12456.78'),
            'availableBalance': Decimal('11956.78'),
            'pendingTransactions': Decimal('500.00'),
            'currency': 'USD',
            'status': 'Active',
            'openedDate': '2018-06-20',
            'interestRate': Decimal('0.01'),
            'minimumBalance': Decimal('25.00')
        },
        {
            'accountId': 'ACC-SAV-002',
            'customerId': 'CUST-10002',
            'accountType': 'Savings',
            'accountNumber': '****3456',
            'accountNumberFull': '4532345678903456',
            'routingNumber': '102000076',
            'balance': Decimal('45678.90'),
            'availableBalance': Decimal('45678.90'),
            'pendingTransactions': Decimal('0.00'),
            'currency': 'USD',
            'status': 'Active',
            'openedDate': '2018-06-20',
            'interestRate': Decimal('0.45'),
            'minimumBalance': Decimal('500.00')
        },
        # Sarah's accounts
        {
            'accountId': 'ACC-CHK-003',
            'customerId': 'CUST-10003',
            'accountType': 'Checking',
            'accountNumber': '****7890',
            'accountNumberFull': '4532789012347890',
            'routingNumber': '102000076',
            'balance': Decimal('2341.15'),
            'availableBalance': Decimal('2141.15'),
            'pendingTransactions': Decimal('200.00'),
            'currency': 'USD',
            'status': 'Active',
            'openedDate': '2021-03-10',
            'interestRate': Decimal('0.01'),
            'minimumBalance': Decimal('25.00')
        }
    ]

    for account in account_data:
        accounts.put_item(Item=account)

    print(f"Accounts seeded: {len(account_data)} accounts")

    # --- 5. Seed Transactions ---
    print("\n--- Seeding Transactions ---")
    transactions = dynamodb.Table('Banking_Transactions')

    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    two_days_ago = today - datetime.timedelta(days=2)

    transaction_data = [
        # Jennifer's recent transactions
        {
            'transactionId': 'TXN-20260127-001',
            'accountId': 'ACC-CHK-001',
            'customerId': 'CUST-10001',
            'date': today.strftime('%Y-%m-%d'),
            'postedDate': None,  # Pending
            'description': 'PENDING: Amazon.com Purchase',
            'merchant': 'Amazon.com',
            'category': 'Shopping',
            'amount': Decimal('-200.00'),
            'balance': Decimal('5847.32'),
            'status': 'Pending',
            'type': 'Debit',
            'channel': 'Online'
        },
        {
            'transactionId': 'TXN-20260126-001',
            'accountId': 'ACC-CHK-001',
            'customerId': 'CUST-10001',
            'date': yesterday.strftime('%Y-%m-%d'),
            'postedDate': yesterday.strftime('%Y-%m-%d'),
            'description': 'SQ*COFFEE SHOP',
            'merchant': 'Local Coffee Shop',
            'merchantCode': 'SQ*ABC123',
            'category': 'Food & Dining',
            'amount': Decimal('-5.75'),
            'balance': Decimal('6047.32'),
            'status': 'Posted',
            'type': 'Debit',
            'channel': 'POS'
        },
        {
            'transactionId': 'TXN-20260125-001',
            'accountId': 'ACC-CHK-001',
            'customerId': 'CUST-10001',
            'date': two_days_ago.strftime('%Y-%m-%d'),
            'postedDate': two_days_ago.strftime('%Y-%m-%d'),
            'description': 'Paycheck Deposit',
            'merchant': 'Employer Inc',
            'category': 'Income',
            'amount': Decimal('3500.00'),
            'balance': Decimal('6053.07'),
            'status': 'Posted',
            'type': 'Credit',
            'channel': 'ACH'
        },
        # Robert's transactions
        {
            'transactionId': 'TXN-20260127-002',
            'accountId': 'ACC-CHK-002',
            'customerId': 'CUST-10002',
            'date': today.strftime('%Y-%m-%d'),
            'postedDate': None,
            'description': 'PENDING: Whole Foods',
            'merchant': 'Whole Foods Market',
            'category': 'Groceries',
            'amount': Decimal('-156.42'),
            'balance': Decimal('12456.78'),
            'status': 'Pending',
            'type': 'Debit',
            'channel': 'POS'
        },
        {
            'transactionId': 'TXN-20260126-002',
            'accountId': 'ACC-CHK-002',
            'customerId': 'CUST-10002',
            'date': yesterday.strftime('%Y-%m-%d'),
            'postedDate': yesterday.strftime('%Y-%m-%d'),
            'description': 'Shell Gas Station',
            'merchant': 'Shell',
            'category': 'Gas',
            'amount': Decimal('-65.00'),
            'balance': Decimal('12613.20'),
            'status': 'Posted',
            'type': 'Debit',
            'channel': 'POS'
        }
    ]

    for txn in transaction_data:
        transactions.put_item(Item=txn)

    print(f"Transactions seeded: {len(transaction_data)} transactions")

    # --- 6. Seed Cards ---
    print("\n--- Seeding Cards ---")
    cards = dynamodb.Table('Banking_Cards')

    card_data = [
        {
            'cardId': 'CARD-001',
            'customerId': 'CUST-10001',
            'accountId': 'ACC-CHK-001',
            'cardNumber': '****1234',
            'cardType': 'Debit',
            'status': 'Active',
            'expirationDate': '12/2027',
            'issueDate': '2023-01-15',
            'cardNetwork': 'Visa',
            'frozen': False,
            'lostStolen': False,
            'replacementStatus': None
        },
        {
            'cardId': 'CARD-002',
            'customerId': 'CUST-10002',
            'accountId': 'ACC-CHK-002',
            'cardNumber': '****9012',
            'cardType': 'Debit',
            'status': 'Active',
            'expirationDate': '08/2026',
            'issueDate': '2021-08-10',
            'cardNetwork': 'Visa',
            'frozen': False,
            'lostStolen': False,
            'replacementStatus': None
        },
        {
            'cardId': 'CARD-003',
            'customerId': 'CUST-10003',
            'accountId': 'ACC-CHK-003',
            'cardNumber': '****7890',
            'cardType': 'Debit',
            'status': 'Frozen',  # User froze it
            'expirationDate': '05/2028',
            'issueDate': '2024-05-01',
            'cardNetwork': 'Visa',
            'frozen': True,
            'frozenDate': (datetime.datetime.now() - datetime.timedelta(days=2)).isoformat(),
            'frozenReason': 'Customer request',
            'lostStolen': False,
            'replacementStatus': None
        }
    ]

    for card in card_data:
        cards.put_item(Item=card)

    print(f"Cards seeded: {len(card_data)} cards")

    # --- 7. Seed Disputes ---
    print("\n--- Seeding Disputes ---")
    disputes = dynamodb.Table('Banking_Disputes')

    dispute_data = [
        {
            'disputeId': 'DISP-20260120-001',
            'customerId': 'CUST-10002',
            'accountId': 'ACC-CHK-002',
            'transactionId': 'TXN-OLD-001',
            'amount': Decimal('299.99'),
            'merchant': 'Unknown Online Store',
            'disputeReason': 'Unauthorized charge',
            'status': 'Under Investigation',
            'filedDate': '2026-01-20T10:30:00Z',
            'expectedResolutionDate': '2026-02-19',  # 30 days
            'provisionalCreditIssued': True,
            'provisionalCreditAmount': Decimal('299.99'),
            'provisionalCreditDate': '2026-01-22',
            'caseNumber': 'CASE-12345',
            'nextSteps': 'Bank investigating with merchant. No action needed from customer at this time.',
            'timeline': '10 business days for merchant response, 30 days total resolution',
            'updatedAt': '2026-01-25T14:00:00Z'
        }
    ]

    for dispute in dispute_data:
        disputes.put_item(Item=dispute)

    print(f"Disputes seeded: {len(dispute_data)} disputes")

    # --- 8. Seed Transfers ---
    print("\n--- Seeding Transfers ---")
    transfers = dynamodb.Table('Banking_Transfers')

    transfer_data = [
        {
            'transferId': 'XFER-20260127-001',
            'customerId': 'CUST-10001',
            'fromAccountId': 'ACC-CHK-001',
            'toAccountId': 'ACC-SAV-001',
            'amount': Decimal('500.00'),
            'transferType': 'Internal',  # Internal, ACH, Wire, Zelle
            'status': 'Completed',
            'scheduledDate': today.strftime('%Y-%m-%d'),
            'completedDate': today.strftime('%Y-%m-%d'),
            'description': 'Transfer to savings',
            'initiatedAt': datetime.datetime.now().isoformat()
        },
        {
            'transferId': 'XFER-20260126-001',
            'customerId': 'CUST-10002',
            'fromAccountId': 'ACC-CHK-002',
            'toAccountId': None,
            'toEmail': 'friend@email.com',
            'amount': Decimal('50.00'),
            'transferType': 'Zelle',
            'status': 'Pending',
            'scheduledDate': yesterday.strftime('%Y-%m-%d'),
            'completedDate': None,
            'description': 'Zelle payment to friend',
            'initiatedAt': (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat()
        }
    ]

    for transfer in transfer_data:
        transfers.put_item(Item=transfer)

    print(f"Transfers seeded: {len(transfer_data)} transfers")

    # --- 9. Seed Auth Sessions ---
    print("\n--- Seeding Auth Sessions ---")
    auth_sessions = dynamodb.Table('Banking_AuthSessions')

    # Current active session
    auth_sessions.put_item(Item={
        'sessionId': 'SESSION-ACTIVE-001',
        'customerId': 'CUST-10001',
        'phone': '+1-555-234-5678',
        'authLevel': 'Level1',  # Level1 (phone), Level2 (phone+OTP), Level3 (phone+OTP+knowledge)
        'authFactors': ['Phone'],
        'mfaCompleted': False,
        'otpSent': False,
        'otpCode': None,
        'knowledgeAnswered': [],
        'sessionStart': datetime.datetime.now().isoformat(),
        'lastActivity': datetime.datetime.now().isoformat(),
        'expiresAt': (datetime.datetime.now() + datetime.timedelta(minutes=30)).isoformat(),
        'ipAddress': '192.168.1.100',
        'jurisdiction': 'US-CO',
        'disclosureAcknowledged': True,
        'consentRecorded': True
    })

    print("Auth sessions seeded: 1 active session")

    # --- 10. Seed Audit Logs ---
    print("\n--- Seeding Audit Logs ---")
    audit_logs = dynamodb.Table('Banking_AuditLogs')

    # Sample audit entries
    audit_entries = [
        {
            'auditId': f'AUDIT-{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}-001',
            'timestamp': datetime.datetime.now().isoformat(),
            'customerId': 'CUST-10001',
            'sessionId': 'SESSION-ACTIVE-001',
            'action': 'CHECK_BALANCE',
            'resource': 'ACC-CHK-001',
            'result': 'SUCCESS',
            'authLevel': 'Level1',
            'ipAddress': '192.168.1.100',
            'jurisdiction': 'US-CO',
            'pii_accessed': False,
            'compliance_flags': []
        }
    ]

    for entry in audit_entries:
        audit_logs.put_item(Item=entry)

    print(f"Audit logs seeded: {len(audit_entries)} entries")

    # --- 11. Seed Consents ---
    print("\n--- Seeding Consents ---")
    consents = dynamodb.Table('Banking_Consents')

    consent_data = [
        {
            'consentId': 'CONSENT-001',
            'customerId': 'CUST-10001',
            'sessionId': 'SESSION-ACTIVE-001',
            'consentType': 'call_recording',
            'consentText': 'This call may be recorded for quality and training purposes. Do you consent to recording?',
            'consentGiven': True,
            'timestamp': datetime.datetime.now().isoformat(),
            'jurisdiction': 'US-CO',
            'ipAddress': '192.168.1.100'
        },
        {
            'consentId': 'CONSENT-002',
            'customerId': 'CUST-10001',
            'sessionId': 'SESSION-ACTIVE-001',
            'consentType': 'data_processing',
            'consentText': 'We will process your request. This may involve accessing your account information.',
            'consentGiven': True,
            'timestamp': datetime.datetime.now().isoformat(),
            'jurisdiction': 'US-CO',
            'ipAddress': '192.168.1.100'
        }
    ]

    for consent in consent_data:
        consents.put_item(Item=consent)

    print(f"Consents seeded: {len(consent_data)} consent records")

    # --- 12. Seed Bill Pay ---
    print("\n--- Seeding Bill Pay ---")
    billpay = dynamodb.Table('Banking_BillPay')

    billpay_data = [
        {
            'payeeId': 'PAYEE-001',
            'customerId': 'CUST-10001',
            'payeeName': 'Electric Company',
            'accountNumber': '****5678',
            'payeeAddress': '123 Utility St, Denver, CO 80202',
            'paymentMethod': 'Electronic',
            'recurringPayment': True,
            'amount': Decimal('125.00'),
            'frequency': 'Monthly',
            'nextPaymentDate': '2026-02-05',
            'fromAccountId': 'ACC-CHK-001',
            'status': 'Active'
        },
        {
            'payeeId': 'PAYEE-002',
            'customerId': 'CUST-10001',
            'payeeName': 'Credit Card Payment',
            'accountNumber': '****1234',
            'payeeAddress': 'PO Box 9999, New York, NY 10001',
            'paymentMethod': 'Electronic',
            'recurringPayment': False,
            'amount': None,
            'frequency': None,
            'nextPaymentDate': None,
            'fromAccountId': 'ACC-CHK-001',
            'status': 'Active'
        }
    ]

    for payee in billpay_data:
        billpay.put_item(Item=payee)

    print(f"Bill pay seeded: {len(billpay_data)} payees")

    print("\n--- Banking Database Setup Complete ---")
    print("\nTest Scenarios:")
    print("1. Authentication: Jennifer Martinez (CUST-10001) - Phone +1-555-234-5678")
    print("2. Check Balance: ACC-CHK-001 (Available: $5,647.32)")
    print("3. Dispute: Robert Chen has active dispute DISP-20260120-001")
    print("4. Frozen Card: Sarah Thompson's card CARD-003 is frozen")
    print("5. Pending Transaction: Check pending Amazon charge for Jennifer")
    print("6. Transfer: Internal transfer from checking to savings")
    print("\nSECURITY FEATURES:")
    print("- Multi-factor authentication ready (MFA)")
    print("- Audit logging enabled")
    print("- Consent tracking active")
    print("- Progressive authentication (Level1/2/3)")
    print("- Session timeouts configured (30 min)")

if __name__ == '__main__':
    setup_banking_demo_data()
