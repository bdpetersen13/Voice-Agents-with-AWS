"""
Healthcare Appointment Scheduling Agent - Database Setup
Creates and seeds all 10 DynamoDB tables with HIPAA-compliant demo data

IMPORTANT: This script creates demo data for testing purposes only.
In production, patient data must be properly encrypted and handled per HIPAA requirements.
"""
import boto3
import datetime
import uuid
from decimal import Decimal


def setup_healthcare_demo_data():
    """
    Sets up DynamoDB tables for healthcare appointment scheduling agent.
    Creates 10 tables: Patients, Appointments, Providers, Locations, Availability,
                      Insurance, Referrals, Intake_Forms, Audit_Logs, Sessions
    """
    # Initialize DynamoDB resource
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

    # --- 1. Define Table Schemas ---
    tables = {
        'Healthcare_Patients': {
            'KeySchema': [{'AttributeName': 'patientId', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'patientId', 'AttributeType': 'S'}]
        },
        'Healthcare_Appointments': {
            'KeySchema': [{'AttributeName': 'appointmentId', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'appointmentId', 'AttributeType': 'S'}]
        },
        'Healthcare_Providers': {
            'KeySchema': [{'AttributeName': 'providerId', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'providerId', 'AttributeType': 'S'}]
        },
        'Healthcare_Locations': {
            'KeySchema': [{'AttributeName': 'locationId', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'locationId', 'AttributeType': 'S'}]
        },
        'Healthcare_Availability': {
            'KeySchema': [{'AttributeName': 'slotId', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'slotId', 'AttributeType': 'S'}]
        },
        'Healthcare_Insurance': {
            'KeySchema': [{'AttributeName': 'insuranceId', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'insuranceId', 'AttributeType': 'S'}]
        },
        'Healthcare_Referrals': {
            'KeySchema': [{'AttributeName': 'referralId', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'referralId', 'AttributeType': 'S'}]
        },
        'Healthcare_Intake_Forms': {
            'KeySchema': [{'AttributeName': 'intakeId', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'intakeId', 'AttributeType': 'S'}]
        },
        'Healthcare_Audit_Logs': {
            'KeySchema': [{'AttributeName': 'auditLogId', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'auditLogId', 'AttributeType': 'S'}]
        },
        'Healthcare_Sessions': {
            'KeySchema': [{'AttributeName': 'sessionId', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'sessionId', 'AttributeType': 'S'}]
        }
    }

    # --- 2. Delete Old Tables & Create New Ones ---
    print("\n" + "="*60)
    print("🏥 Healthcare Database Setup - HIPAA Compliant")
    print("="*60)
    print("\n--- Resetting Database Tables ---")

    for table_name, schema in tables.items():
        table = dynamodb.Table(table_name)

        # Delete if exists
        try:
            print(f"🗑️  Deleting old table: {table_name}...")
            table.delete()
            table.wait_until_not_exists()
            print(f"   ✓ Deleted {table_name}")
        except Exception as e:
            if "ResourceNotFoundException" in str(e):
                print(f"   ℹ️  Table {table_name} doesn't exist (will create new)")
            else:
                print(f"   ⚠️  Warning deleting {table_name}: {e}")

        # Create new
        print(f"📝 Creating table: {table_name}...")
        try:
            dynamodb.create_table(
                TableName=table_name,
                KeySchema=schema['KeySchema'],
                AttributeDefinitions=schema['AttributeDefinitions'],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )
            table = dynamodb.Table(table_name)
            table.wait_until_exists()
            print(f"   ✓ Ready: {table_name}\n")
        except Exception as e:
            print(f"   ❌ Error creating {table_name}: {e}")
            return

    # Calculate dates for appointments
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)
    next_week = today + datetime.timedelta(days=7)
    two_weeks = today + datetime.timedelta(days=14)
    three_weeks = today + datetime.timedelta(days=21)

    # --- 3. Seed Locations ---
    print("="*60)
    print("📍 Seeding Clinic Locations")
    print("="*60)
    locations = dynamodb.Table('Healthcare_Locations')

    location_data = [
        {
            'locationId': 'LOC-001',
            'name': 'Main Street Clinic',
            'address': '123 Main Street, Boston, MA 02101',
            'city': 'Boston',
            'state': 'MA',
            'zipCode': '02101',
            'phoneNumber': '617-555-1000',
            'servicesOffered': ['primary_care', 'lab', 'imaging', 'pharmacy'],
            'hours': 'Monday-Friday 8:00 AM - 6:00 PM',
            'parking': 'Free parking in main lot'
        },
        {
            'locationId': 'LOC-002',
            'name': 'Downtown Medical Center',
            'address': '456 Medical Plaza, Boston, MA 02102',
            'city': 'Boston',
            'state': 'MA',
            'zipCode': '02102',
            'phoneNumber': '617-555-2000',
            'servicesOffered': ['primary_care', 'cardiology', 'imaging', 'urgent_care', 'lab'],
            'hours': 'Monday-Saturday 7:00 AM - 8:00 PM',
            'parking': 'Parking garage - $5 with validation'
        },
        {
            'locationId': 'LOC-003',
            'name': 'Northside Health Center',
            'address': '789 Oak Avenue, Cambridge, MA 02138',
            'city': 'Cambridge',
            'state': 'MA',
            'zipCode': '02138',
            'phoneNumber': '617-555-3000',
            'servicesOffered': ['primary_care', 'dermatology', 'lab'],
            'hours': 'Monday-Friday 9:00 AM - 5:00 PM',
            'parking': 'Street parking and nearby garage'
        }
    ]

    for location in location_data:
        locations.put_item(Item=location)

    print(f"✓ Locations seeded: {len(location_data)} clinics")
    for loc in location_data:
        print(f"  - {loc['name']} ({loc['city']})")

    # --- 4. Seed Providers ---
    print("\n" + "="*60)
    print("👨‍⚕️ Seeding Healthcare Providers")
    print("="*60)
    providers = dynamodb.Table('Healthcare_Providers')

    provider_data = [
        {
            'providerId': 'PROV-001',
            'name': 'Dr. Sarah Johnson',
            'specialty': 'primary_care',
            'locations': ['LOC-001', 'LOC-002'],
            'acceptingNewPatients': True,
            'phoneNumber': '617-555-1001',
            'email': 'dr.johnson@healthcare.example.com',
            'languages': ['English', 'Spanish'],
            'yearsExperience': 15
        },
        {
            'providerId': 'PROV-002',
            'name': 'Dr. Michael Chen',
            'specialty': 'cardiology',
            'locations': ['LOC-002'],
            'acceptingNewPatients': True,
            'phoneNumber': '617-555-2001',
            'email': 'dr.chen@healthcare.example.com',
            'languages': ['English', 'Mandarin'],
            'yearsExperience': 20
        },
        {
            'providerId': 'PROV-003',
            'name': 'Dr. Emily Rodriguez',
            'specialty': 'dermatology',
            'locations': ['LOC-003'],
            'acceptingNewPatients': True,
            'phoneNumber': '617-555-3001',
            'email': 'dr.rodriguez@healthcare.example.com',
            'languages': ['English'],
            'yearsExperience': 8
        },
        {
            'providerId': 'PROV-004',
            'name': 'Dr. James Williams',
            'specialty': 'primary_care',
            'locations': ['LOC-001', 'LOC-003'],
            'acceptingNewPatients': False,  # Not accepting new patients
            'phoneNumber': '617-555-1002',
            'email': 'dr.williams@healthcare.example.com',
            'languages': ['English'],
            'yearsExperience': 25
        }
    ]

    for provider in provider_data:
        providers.put_item(Item=provider)

    print(f"✓ Providers seeded: {len(provider_data)} doctors")
    for prov in provider_data:
        accepting = "✓ Accepting new" if prov['acceptingNewPatients'] else "✗ Not accepting new"
        print(f"  - {prov['name']} ({prov['specialty']}) - {accepting}")

    # --- 5. Seed Availability (Appointment Slots) ---
    print("\n" + "="*60)
    print("📅 Seeding Appointment Availability")
    print("="*60)
    availability = dynamodb.Table('Healthcare_Availability')

    # Generate slots for next 3 weeks
    slot_count = 0
    for days_ahead in range(1, 22):  # Next 3 weeks
        date = today + datetime.timedelta(days=days_ahead)
        date_str = date.strftime('%Y-%m-%d')

        # Skip weekends for most providers
        if date.weekday() >= 5:  # Saturday = 5, Sunday = 6
            continue

        # Morning slots (9:00 AM - 12:00 PM)
        morning_times = ['09:00', '09:30', '10:00', '10:30', '11:00', '11:30']
        # Afternoon slots (1:00 PM - 5:00 PM)
        afternoon_times = ['13:00', '13:30', '14:00', '14:30', '15:00', '15:30', '16:00', '16:30']

        all_times = morning_times + afternoon_times

        # Create slots for Dr. Johnson (primary care) at LOC-001
        for time in all_times[:10]:  # 10 slots per day
            slot_count += 1
            availability.put_item(Item={
                'slotId': f'SLOT-{slot_count:05d}',
                'providerId': 'PROV-001',
                'providerName': 'Dr. Sarah Johnson',
                'locationId': 'LOC-001',
                'locationName': 'Main Street Clinic',
                'date': date_str,
                'startTime': time,
                'duration': 30,  # minutes
                'appointmentType': 'primary_care',
                'status': 'AVAILABLE'
            })

        # Create slots for Dr. Chen (cardiology) at LOC-002
        for time in all_times[::2][:6]:  # 6 slots per day (every 2nd slot)
            slot_count += 1
            availability.put_item(Item={
                'slotId': f'SLOT-{slot_count:05d}',
                'providerId': 'PROV-002',
                'providerName': 'Dr. Michael Chen',
                'locationId': 'LOC-002',
                'locationName': 'Downtown Medical Center',
                'date': date_str,
                'startTime': time,
                'duration': 45,  # Cardiology appointments are longer
                'appointmentType': 'cardiology',
                'status': 'AVAILABLE'
            })

    print(f"✓ Availability seeded: {slot_count} appointment slots over 3 weeks")

    # --- 6. Seed Patients ---
    print("\n" + "="*60)
    print("👤 Seeding Patients (Demo Data)")
    print("="*60)
    patients = dynamodb.Table('Healthcare_Patients')

    patient_data = [
        {
            'patientId': 'PAT-10001',
            'firstName': 'John',
            'lastName': 'Smith',
            'dateOfBirth': '1980-01-15',
            'phoneNumber': '617-555-4001',
            'email': 'john.smith@example.com',
            'address': '100 Elm Street, Boston, MA 02101',
            'insuranceId': 'INS-10001',
            'emergencyContact': {
                'name': 'Jane Smith',
                'relationship': 'Spouse',
                'phone': '617-555-4002'
            },
            'authorizedProxies': []  # No proxies authorized
        },
        {
            'patientId': 'PAT-10002',
            'firstName': 'Maria',
            'lastName': 'Garcia',
            'dateOfBirth': '1992-06-22',
            'phoneNumber': '617-555-4003',
            'email': 'maria.garcia@example.com',
            'address': '200 Pine Street, Cambridge, MA 02138',
            'insuranceId': 'INS-10002',
            'emergencyContact': {
                'name': 'Carlos Garcia',
                'relationship': 'Father',
                'phone': '617-555-4004'
            },
            'authorizedProxies': ['Carlos Garcia']
        },
        {
            'patientId': 'PAT-10003',
            'firstName': 'Emma',
            'lastName': 'Wilson',
            'dateOfBirth': '2015-03-10',  # Minor (9 years old)
            'phoneNumber': '617-555-4005',
            'email': 'parent@example.com',
            'address': '300 Oak Avenue, Boston, MA 02102',
            'insuranceId': 'INS-10003',
            'emergencyContact': {
                'name': 'Jennifer Wilson',
                'relationship': 'Mother',
                'phone': '617-555-4005'
            },
            'authorizedProxies': ['Jennifer Wilson', 'David Wilson']  # Parents
        },
        {
            'patientId': 'PAT-10004',
            'firstName': 'Robert',
            'lastName': 'Taylor',
            'dateOfBirth': '1955-11-08',
            'phoneNumber': '617-555-4006',
            'email': 'robert.taylor@example.com',
            'address': '400 Maple Drive, Boston, MA 02101',
            'insuranceId': 'INS-10004',
            'emergencyContact': {
                'name': 'Sarah Taylor',
                'relationship': 'Daughter',
                'phone': '617-555-4007'
            },
            'authorizedProxies': ['Sarah Taylor']  # Power of attorney
        }
    ]

    for patient in patient_data:
        patients.put_item(Item=patient)

    print(f"✓ Patients seeded: {len(patient_data)} patients")
    for pat in patient_data:
        age = (today - datetime.datetime.strptime(pat['dateOfBirth'], '%Y-%m-%d').date()).days // 365
        print(f"  - {pat['firstName']} {pat['lastName']} (DOB: {pat['dateOfBirth']}, Age: {age})")

    # --- 7. Seed Insurance ---
    print("\n" + "="*60)
    print("💳 Seeding Insurance Records")
    print("="*60)
    insurance = dynamodb.Table('Healthcare_Insurance')

    insurance_data = [
        {
            'insuranceId': 'INS-10001',
            'provider': 'Blue Cross Blue Shield',
            'memberId': 'BCBS123456789',
            'groupNumber': 'GRP001',
            'status': 'ACTIVE',
            'copay': Decimal('25.00'),
            'deductible': Decimal('1500.00'),
            'deductibleMet': Decimal('800.00'),
            'requiresPreAuth': ['imaging', 'surgery']
        },
        {
            'insuranceId': 'INS-10002',
            'provider': 'Aetna',
            'memberId': 'AETNA987654321',
            'groupNumber': 'GRP002',
            'status': 'ACTIVE',
            'copay': Decimal('30.00'),
            'deductible': Decimal('2000.00'),
            'deductibleMet': Decimal('0.00'),
            'requiresPreAuth': ['surgery', 'specialist']
        },
        {
            'insuranceId': 'INS-10003',
            'provider': 'United Healthcare',
            'memberId': 'UHC456123789',
            'groupNumber': 'GRP003',
            'status': 'ACTIVE',
            'copay': Decimal('20.00'),
            'deductible': Decimal('1000.00'),
            'deductibleMet': Decimal('1000.00'),  # Fully met
            'requiresPreAuth': []
        },
        {
            'insuranceId': 'INS-10004',
            'provider': 'Medicare',
            'memberId': 'MEDICARE111222333',
            'groupNumber': 'N/A',
            'status': 'ACTIVE',
            'copay': Decimal('0.00'),  # Medicare covers most
            'deductible': Decimal('250.00'),
            'deductibleMet': Decimal('250.00'),  # Met
            'requiresPreAuth': ['imaging']
        }
    ]

    for ins in insurance_data:
        insurance.put_item(Item=ins)

    print(f"✓ Insurance records seeded: {len(insurance_data)} records")
    for ins in insurance_data:
        print(f"  - {ins['provider']} (Copay: ${ins['copay']})")

    # --- 8. Seed Referrals ---
    print("\n" + "="*60)
    print("📋 Seeding Referral Records")
    print("="*60)
    referrals = dynamodb.Table('Healthcare_Referrals')

    referral_data = [
        {
            'referralId': 'REF-001',
            'patientId': 'PAT-10002',
            'specialty': 'cardiology',
            'referringProvider': 'Dr. Sarah Johnson',
            'referringProviderId': 'PROV-001',
            'status': 'ACTIVE',
            'dateIssued': (today - datetime.timedelta(days=5)).strftime('%Y-%m-%d'),
            'expirationDate': (today + datetime.timedelta(days=90)).strftime('%Y-%m-%d'),
            'authorizationNumber': 'AUTH-2024-001'
        },
        {
            'referralId': 'REF-002',
            'patientId': 'PAT-10004',
            'specialty': 'dermatology',
            'referringProvider': 'Dr. James Williams',
            'referringProviderId': 'PROV-004',
            'status': 'ACTIVE',
            'dateIssued': (today - datetime.timedelta(days=10)).strftime('%Y-%m-%d'),
            'expirationDate': (today + datetime.timedelta(days=80)).strftime('%Y-%m-%d'),
            'authorizationNumber': 'AUTH-2024-002'
        }
    ]

    for ref in referral_data:
        referrals.put_item(Item=ref)

    print(f"✓ Referrals seeded: {len(referral_data)} active referrals")
    for ref in referral_data:
        print(f"  - {ref['specialty']} for Patient {ref['patientId']}")

    # --- 9. Seed Sample Appointments ---
    print("\n" + "="*60)
    print("🗓️  Seeding Sample Appointments")
    print("="*60)
    appointments = dynamodb.Table('Healthcare_Appointments')

    appointment_data = [
        {
            'appointmentId': f'APPT-{tomorrow.strftime("%Y%m%d")}-001',
            'patientId': 'PAT-10001',
            'patientName': 'John Smith',
            'providerId': 'PROV-001',
            'providerName': 'Dr. Sarah Johnson',
            'locationId': 'LOC-001',
            'locationName': 'Main Street Clinic',
            'date': tomorrow.strftime('%Y-%m-%d'),
            'startTime': '10:00',
            'duration': 30,
            'appointmentType': 'follow_up',
            'status': 'CONFIRMED',
            'reasonCategory': 'follow_up',
            'createdAt': (today - datetime.timedelta(days=7)).strftime('%Y-%m-%d'),
            'confirmedAt': (today - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        },
        {
            'appointmentId': f'APPT-{next_week.strftime("%Y%m%d")}-002',
            'patientId': 'PAT-10002',
            'patientName': 'Maria Garcia',
            'providerId': 'PROV-002',
            'providerName': 'Dr. Michael Chen',
            'locationId': 'LOC-002',
            'locationName': 'Downtown Medical Center',
            'date': next_week.strftime('%Y-%m-%d'),
            'startTime': '14:00',
            'duration': 45,
            'appointmentType': 'new_patient',
            'status': 'SCHEDULED',
            'reasonCategory': 'new_concern',
            'createdAt': (today - datetime.timedelta(days=2)).strftime('%Y-%m-%d')
        }
    ]

    for appt in appointment_data:
        appointments.put_item(Item=appt)

    print(f"✓ Appointments seeded: {len(appointment_data)} upcoming appointments")
    for appt in appointment_data:
        print(f"  - {appt['patientName']} with {appt['providerName']} on {appt['date']} at {appt['startTime']}")

    # --- 10. Initialize Empty Tables (Intake, Audit, Sessions) ---
    print("\n" + "="*60)
    print("📝 Initializing Empty Tables")
    print("="*60)
    print("✓ Healthcare_Intake_Forms: Empty (created on demand)")
    print("✓ Healthcare_Audit_Logs: Empty (populated during operation)")
    print("✓ Healthcare_Sessions: Empty (created on agent startup)")

    # --- Setup Complete ---
    print("\n" + "="*60)
    print("✅ Healthcare Database Setup Complete!")
    print("="*60)
    print("\nSummary:")
    print(f"  📍 Locations: {len(location_data)} clinics")
    print(f"  👨‍⚕️ Providers: {len(provider_data)} doctors")
    print(f"  📅 Availability: {slot_count} appointment slots")
    print(f"  👤 Patients: {len(patient_data)} patients")
    print(f"  💳 Insurance: {len(insurance_data)} records")
    print(f"  📋 Referrals: {len(referral_data)} active referrals")
    print(f"  🗓️  Appointments: {len(appointment_data)} scheduled")
    print("\n🎉 Ready to run healthcare_agent.py!\n")
    print("Testing scenarios available:")
    print("  1. Schedule appointment for John Smith (PAT-10001)")
    print("  2. Verify identity for Maria Garcia (PAT-10002)")
    print("  3. Proxy access for Emma Wilson (minor, PAT-10003)")
    print("  4. Check referral for cardiology (Maria has active referral)")
    print("  5. Search availability with Dr. Sarah Johnson")
    print("\n" + "="*60 + "\n")


if __name__ == '__main__':
    print("\n⚠️  HIPAA NOTICE:")
    print("This script creates DEMO DATA for testing purposes only.")
    print("Do NOT use this data in production environments.")
    print("All patient data must be properly encrypted and handled per HIPAA.\n")

    response = input("Continue with database setup? (yes/no): ")
    if response.lower() == 'yes':
        setup_healthcare_demo_data()
    else:
        print("Setup cancelled.")
