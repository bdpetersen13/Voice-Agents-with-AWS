"""
Banking Authentication Manager
Handles multi-factor authentication and progressive authentication levels
"""
import datetime
import hashlib
import random
from boto3.dynamodb.conditions import Attr
from config.constants import *
from config.settings import get_config


class BankingAuthenticationManager:
    """
    Manages multi-factor authentication and progressive authentication levels.

    Authentication Levels:
    - Level 1: Phone number verified (low-risk operations: check balance, recent transactions)
    - Level 2: Phone + OTP via SMS/App (medium-risk: transfers between own accounts, view full account #)
    - Level 3: Phone + OTP + Knowledge question (high-risk: wire transfers, add external accounts)
    """

    def __init__(self, dynamodb):
        self.dynamodb = dynamodb
        config = get_config()

        # Initialize tables from config
        self.auth_sessions_table = self.dynamodb.Table(config.auth_sessions_table)
        self.customers_table = self.dynamodb.Table(config.customers_table)
        self.audit_logs_table = self.dynamodb.Table(config.audit_logs_table)
        self.consents_table = self.dynamodb.Table(config.consents_table)

    def create_session(self, phone: str):
        """Create new authentication session at Level 1 (phone verified)"""
        config = get_config()

        # Find customer by phone
        response = self.customers_table.scan(FilterExpression=Attr('phone').eq(phone))
        customers = response.get('Items', [])

        if not customers:
            return None

        customer = customers[0]
        session_id = (
            f"{SESSION_ID_PREFIX}-"
            f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-"
            f"{random.randint(RANDOM_SUFFIX_MIN, RANDOM_SUFFIX_MAX)}"
        )

        # Create session
        session = {
            'sessionId': session_id,
            'customerId': customer['customerId'],
            'phone': phone,
            'authLevel': AUTH_LEVEL_1,  # Start at Level 1
            'authFactors': ['Phone'],
            'mfaCompleted': False,
            'otpSent': False,
            'otpCode': None,
            'otpExpiry': None,
            'knowledgeAnswered': [],
            'sessionStart': datetime.datetime.now().isoformat(),
            'lastActivity': datetime.datetime.now().isoformat(),
            'expiresAt': (
                datetime.datetime.now() +
                datetime.timedelta(minutes=config.session_timeout_minutes)
            ).isoformat(),
            'ipAddress': '192.168.1.100',  # Would be actual IP in production
            'jurisdiction': customer.get('jurisdiction', 'US'),
            'disclosureAcknowledged': False,
            'consentRecorded': False
        }

        self.auth_sessions_table.put_item(Item=session)

        # Log session creation
        self._audit_log(
            session_id,
            customer['customerId'],
            'SESSION_CREATED',
            None,
            AUDIT_RESULT_SUCCESS,
            AUTH_LEVEL_1
        )

        return session

    def get_session(self, session_id: str):
        """Retrieve session and check if expired"""
        response = self.auth_sessions_table.get_item(Key={'sessionId': session_id})
        if 'Item' not in response:
            return None

        session = response['Item']

        # Check expiry
        expiry = datetime.datetime.fromisoformat(session['expiresAt'])
        if datetime.datetime.now() > expiry:
            return None

        return session

    def update_last_activity(self, session_id: str):
        """Update last activity timestamp (extends session)"""
        self.auth_sessions_table.update_item(
            Key={'sessionId': session_id},
            UpdateExpression="SET lastActivity = :now",
            ExpressionAttributeValues={':now': datetime.datetime.now().isoformat()}
        )

    def send_otp(self, session_id: str):
        """Generate and 'send' OTP (simulated - in production would use SNS/Twilio)"""
        config = get_config()
        session = self.get_session(session_id)

        if not session:
            return {'success': False, 'message': 'Session not found or expired'}

        # Generate OTP using constants
        otp = str(random.randint(OTP_MIN_VALUE, OTP_MAX_VALUE))
        otp_expiry = datetime.datetime.now() + datetime.timedelta(minutes=config.otp_expiry_minutes)

        # Update session with OTP
        self.auth_sessions_table.update_item(
            Key={'sessionId': session_id},
            UpdateExpression="SET otpSent = :true, otpCode = :otp, otpExpiry = :expiry",
            ExpressionAttributeValues={
                ':true': True,
                ':otp': otp,
                ':expiry': otp_expiry.isoformat()
            }
        )

        # In production, send via SMS/app push notification
        print(f"[SECURITY] OTP sent to {session['phone']}: {otp}")

        self._audit_log(
            session_id,
            session['customerId'],
            'OTP_SENT',
            None,
            AUDIT_RESULT_SUCCESS,
            session['authLevel']
        )

        return {
            'success': True,
            'message': f'OTP sent to {session["phone"]}',
            'otp': otp  # Remove otp in production!
        }

    def verify_otp(self, session_id: str, provided_otp: str):
        """Verify OTP and upgrade to Level 2"""
        session = self.get_session(session_id)

        if not session:
            return {'success': False, 'message': 'Session not found or expired'}

        if not session.get('otpSent'):
            return {'success': False, 'message': 'No OTP was sent'}

        # Check OTP expiry
        otp_expiry = datetime.datetime.fromisoformat(session['otpExpiry'])
        if datetime.datetime.now() > otp_expiry:
            return {'success': False, 'message': 'OTP expired. Please request a new one.'}

        # Verify OTP
        if provided_otp != session['otpCode']:
            self._audit_log(
                session_id,
                session['customerId'],
                'OTP_VERIFY_FAILED',
                None,
                AUDIT_RESULT_FAILURE,
                session['authLevel']
            )
            return {'success': False, 'message': 'Incorrect OTP'}

        # Upgrade to Level 2
        self.auth_sessions_table.update_item(
            Key={'sessionId': session_id},
            UpdateExpression="SET authLevel = :level2, mfaCompleted = :true, authFactors = :factors",
            ExpressionAttributeValues={
                ':level2': AUTH_LEVEL_2,
                ':true': True,
                ':factors': ['Phone', 'OTP']
            }
        )

        self._audit_log(
            session_id,
            session['customerId'],
            'OTP_VERIFIED',
            None,
            AUDIT_RESULT_SUCCESS,
            AUTH_LEVEL_2
        )

        return {
            'success': True,
            'message': 'OTP verified. Authentication upgraded to Level 2.'
        }

    def ask_knowledge_question(self, session_id: str):
        """Ask knowledge-based authentication question"""
        session = self.get_session(session_id)
        if not session:
            return None

        # Get customer security questions
        response = self.customers_table.get_item(Key={'customerId': session['customerId']})
        if 'Item' not in response:
            return None

        customer = response['Item']

        # Pick a random security question (in production, pick one not recently used)
        questions = {
            'mothersMaidenName': "What is your mother's maiden name?",
            'firstPetName': "What was the name of your first pet?",
            'lastTransaction': "What was the last purchase you made?"  # Dynamic question
        }

        # For demo, use mother's maiden name
        return {
            'question': questions['mothersMaidenName'],
            'questionType': 'mothersMaidenName'
        }

    def verify_knowledge_answer(self, session_id: str, question_type: str, answer: str):
        """Verify knowledge question and upgrade to Level 3"""
        session = self.get_session(session_id)
        if not session:
            return {'success': False, 'message': 'Session not found or expired'}

        # Get customer
        response = self.customers_table.get_item(Key={'customerId': session['customerId']})
        if 'Item' not in response:
            return {'success': False, 'message': 'Customer not found'}

        customer = response['Item']

        # Hash the provided answer
        hashed_answer = hashlib.sha256(answer.encode()).hexdigest()

        # Verify answer
        stored_hash = customer['securityQuestions'].get(question_type)
        if hashed_answer != stored_hash:
            self._audit_log(
                session_id,
                session['customerId'],
                'KNOWLEDGE_AUTH_FAILED',
                None,
                AUDIT_RESULT_FAILURE,
                session['authLevel']
            )
            return {'success': False, 'message': 'Incorrect answer'}

        # Upgrade to Level 3
        self.auth_sessions_table.update_item(
            Key={'sessionId': session_id},
            UpdateExpression="SET authLevel = :level3, knowledgeAnswered = list_append(knowledgeAnswered, :q), authFactors = :factors",
            ExpressionAttributeValues={
                ':level3': AUTH_LEVEL_3,
                ':q': [question_type],
                ':factors': ['Phone', 'OTP', 'Knowledge']
            }
        )

        self._audit_log(
            session_id,
            session['customerId'],
            'KNOWLEDGE_AUTH_SUCCESS',
            None,
            AUDIT_RESULT_SUCCESS,
            AUTH_LEVEL_3
        )

        return {
            'success': True,
            'message': 'Knowledge verification successful. Authentication upgraded to Level 3.'
        }

    def check_auth_level(self, session_id: str, required_level: str):
        """
        Check if session has required authentication level.
        Returns (authorized: bool, message: str, current_level: str)
        """
        session = self.get_session(session_id)
        if not session:
            return (False, 'Session not found or expired. Please authenticate again.', None)

        current_level = session['authLevel']

        # Map levels to numeric values
        level_hierarchy = {
            AUTH_LEVEL_1: 1,
            AUTH_LEVEL_2: 2,
            AUTH_LEVEL_3: 3
        }

        current_level_num = level_hierarchy.get(current_level, 0)
        required_level_num = level_hierarchy.get(required_level, 0)

        if current_level_num >= required_level_num:
            # Update last activity
            self.update_last_activity(session_id)
            return (True, f'Authorized at {current_level}', current_level)
        else:
            # Step-up authentication required
            if required_level == AUTH_LEVEL_2 and current_level == AUTH_LEVEL_1:
                return (
                    False,
                    'This operation requires multi-factor authentication. Please verify the OTP we are sending to your phone.',
                    current_level
                )
            elif required_level == AUTH_LEVEL_3:
                if current_level == AUTH_LEVEL_1:
                    return (
                        False,
                        'This high-risk operation requires enhanced authentication. Please verify the OTP and answer a security question.',
                        current_level
                    )
                else:  # Level2
                    return (
                        False,
                        'This high-risk operation requires additional verification. Please answer a security question.',
                        current_level
                    )
            else:
                return (
                    False,
                    f'Insufficient authentication level. Current: {current_level}, Required: {required_level}',
                    current_level
                )

    def record_consent(self, session_id: str, consent_type: str, consent_text: str, consent_given: bool):
        """Record user consent for compliance"""
        session = self.get_session(session_id)
        if not session:
            return False

        consent_id = (
            f"CONSENT-"
            f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-"
            f"{random.randint(RANDOM_SUFFIX_MIN, RANDOM_SUFFIX_MAX)}"
        )

        consent = {
            'consentId': consent_id,
            'customerId': session['customerId'],
            'sessionId': session_id,
            'consentType': consent_type,
            'consentText': consent_text,
            'consentGiven': consent_given,
            'timestamp': datetime.datetime.now().isoformat(),
            'jurisdiction': session.get('jurisdiction', 'US'),
            'ipAddress': session.get('ipAddress')
        }

        self.consents_table.put_item(Item=consent)

        # Update session
        self.auth_sessions_table.update_item(
            Key={'sessionId': session_id},
            UpdateExpression="SET consentRecorded = :true",
            ExpressionAttributeValues={':true': True}
        )

        return True

    def _audit_log(self, session_id, customer_id, action, resource, result, auth_level, pii_accessed=False):
        """Create immutable audit log entry"""
        config = get_config()
        audit_id = (
            f"AUDIT-"
            f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}-"
            f"{random.randint(1000, 9999)}"
        )

        session = self.get_session(session_id) if session_id else None

        log_entry = {
            'auditId': audit_id,
            'timestamp': datetime.datetime.now().isoformat(),
            'customerId': customer_id,
            'sessionId': session_id,
            'action': action,
            'resource': resource,
            'result': result,
            'authLevel': auth_level,
            'ipAddress': session.get('ipAddress') if session else None,
            'jurisdiction': session.get('jurisdiction') if session else None,
            'pii_accessed': pii_accessed,
            'compliance_flags': []
        }

        self.audit_logs_table.put_item(Item=log_entry)

        if config.debug_mode:
            print(f"[AUDIT] {action} - {result} - Level: {auth_level}")
