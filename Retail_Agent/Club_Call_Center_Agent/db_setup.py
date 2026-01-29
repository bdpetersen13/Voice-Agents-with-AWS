import boto3
import datetime
import time
from decimal import Decimal

def setup_call_center_demo_data():
    """
    Sets up DynamoDB tables for a club call center agent.
    Creates tables for: Store_Info, Inventory, Curbside_Orders, Appointments, Specialty_Orders, Members
    """
    # Initialize DynamoDB resource
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

    # --- 1. Define Table Schemas ---
    tables = {
        'CallCenter_Store_Info': {
            'KeySchema': [{'AttributeName': 'storeId', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'storeId', 'AttributeType': 'S'}]
        },
        'CallCenter_Inventory': {
            'KeySchema': [{'AttributeName': 'sku', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'sku', 'AttributeType': 'S'}]
        },
        'CallCenter_Curbside_Orders': {
            'KeySchema': [{'AttributeName': 'orderId', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'orderId', 'AttributeType': 'S'}]
        },
        'CallCenter_Appointments': {
            'KeySchema': [{'AttributeName': 'appointmentId', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'appointmentId', 'AttributeType': 'S'}]
        },
        'CallCenter_Specialty_Orders': {
            'KeySchema': [{'AttributeName': 'orderId', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'orderId', 'AttributeType': 'S'}]
        },
        'CallCenter_Members': {
            'KeySchema': [{'AttributeName': 'memberId', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'memberId', 'AttributeType': 'S'}]
        }
    }

    # --- 2. Delete Old Tables & Create New Ones ---
    print("--- Resetting Call Center Database ---")
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

    # --- 3. Seed Store Info ---
    print("\n--- Seeding Store Information ---")
    store_info = dynamodb.Table('CallCenter_Store_Info')

    today = datetime.date.today()

    # Main store location
    store_info.put_item(Item={
        'storeId': 'STORE-4523',
        'storeName': 'Denver Warehouse Club',
        'location': '1234 Commerce Drive, Denver, CO 80202',
        'phone': '+1-303-555-CLUB',
        'regularHours': {
            'Monday': '9:00 AM - 9:00 PM',
            'Tuesday': '9:00 AM - 9:00 PM',
            'Wednesday': '9:00 AM - 9:00 PM',
            'Thursday': '9:00 AM - 9:00 PM',
            'Friday': '9:00 AM - 9:00 PM',
            'Saturday': '9:00 AM - 7:00 PM',
            'Sunday': '10:00 AM - 6:00 PM'
        },
        'holidayHours': {
            'Thanksgiving': 'CLOSED',
            'Christmas': 'CLOSED',
            'New Years Day': '10:00 AM - 6:00 PM',
            'Memorial Day': '9:00 AM - 7:00 PM',
            'July 4th': '9:00 AM - 7:00 PM',
            'Labor Day': '9:00 AM - 7:00 PM'
        },
        'specialClosures': [],  # For severe weather, etc.
        'departments': {
            'TireCenter': {
                'hours': 'Mon-Fri: 9:00 AM - 7:00 PM, Sat: 9:00 AM - 6:00 PM, Sun: 10:00 AM - 5:00 PM',
                'phone': '+1-303-555-TIRE',
                'appointmentsAvailable': True
            },
            'OpticalCenter': {
                'hours': 'Mon-Fri: 9:00 AM - 7:00 PM, Sat: 9:00 AM - 6:00 PM, Sun: CLOSED',
                'phone': '+1-303-555-EYES',
                'appointmentsAvailable': True
            },
            'HearingAidCenter': {
                'hours': 'Mon-Fri: 10:00 AM - 6:00 PM, Sat: 10:00 AM - 4:00 PM, Sun: CLOSED',
                'phone': '+1-303-555-HEAR',
                'appointmentsAvailable': True
            },
            'Pharmacy': {
                'hours': 'Mon-Fri: 9:00 AM - 7:00 PM, Sat: 9:00 AM - 5:00 PM, Sun: 10:00 AM - 5:00 PM',
                'phone': '+1-303-555-PHRM',
                'appointmentsAvailable': True
            },
            'Bakery': {
                'hours': 'Mon-Sun: 9:00 AM - 7:00 PM',
                'phone': '+1-303-555-CAKE',
                'cakeOrderLeadTime': '48 hours'
            }
        }
    })

    print("Store info seeded: STORE-4523 (Denver)")

    # --- 4. Seed Inventory ---
    print("\n--- Seeding Inventory ---")
    inventory = dynamodb.Table('CallCenter_Inventory')

    # Sample items with stock levels
    items = [
        {
            'sku': 'FOOD-12345',
            'productName': 'Kirkland Organic Almond Milk 12-Pack',
            'category': 'Grocery',
            'inStock': True,
            'quantity': 127,
            'aisleLocation': 'Aisle 12 - Refrigerated',
            'price': Decimal('15.99')
        },
        {
            'sku': 'ELEC-98765',
            'productName': 'Samsung 65" 4K Smart TV',
            'category': 'Electronics',
            'inStock': True,
            'quantity': 8,
            'aisleLocation': 'Electronics Department - TV Wall',
            'price': Decimal('799.99')
        },
        {
            'sku': 'HOME-54321',
            'productName': 'Dyson V15 Cordless Vacuum',
            'category': 'Home & Garden',
            'inStock': False,
            'quantity': 0,
            'aisleLocation': 'Aisle 25 - Home Appliances',
            'price': Decimal('549.99'),
            'expectedRestock': (today + datetime.timedelta(days=5)).strftime('%Y-%m-%d')
        },
        {
            'sku': 'TIRE-11111',
            'productName': 'Michelin Defender All-Season Tire 225/65R17',
            'category': 'Tire Center',
            'inStock': True,
            'quantity': 32,
            'aisleLocation': 'Tire Center Warehouse',
            'price': Decimal('189.99')
        },
        {
            'sku': 'FOOD-99999',
            'productName': 'Rotisserie Chicken',
            'category': 'Deli',
            'inStock': True,
            'quantity': 45,
            'aisleLocation': 'Deli Section - Hot Food',
            'price': Decimal('4.99')
        }
    ]

    for item in items:
        inventory.put_item(Item=item)

    print(f"Inventory seeded: {len(items)} products")

    # --- 5. Seed Curbside Orders ---
    print("\n--- Seeding Curbside Orders ---")
    curbside = dynamodb.Table('CallCenter_Curbside_Orders')

    tomorrow = (today + datetime.timedelta(days=1)).strftime('%Y-%m-%d')

    # Order 1: Ready for pickup
    curbside.put_item(Item={
        'orderId': 'CURB-20260127-001',
        'memberId': 'MEM-100001',
        'memberName': 'Sarah Chen',
        'orderDate': today.strftime('%Y-%m-%d'),
        'orderTime': '09:15:00',
        'status': 'Ready for Pickup',
        'pickupInstructions': 'Park in designated curbside spots 1-10. Call when you arrive.',
        'items': [
            {'sku': 'FOOD-12345', 'name': 'Organic Almond Milk 12-Pack', 'quantity': 2},
            {'sku': 'FOOD-99999', 'name': 'Rotisserie Chicken', 'quantity': 1}
        ],
        'total': Decimal('36.97'),
        'estimatedPickupTime': '12:00 PM - 2:00 PM',
        'readyTime': '11:45 AM'
    })

    # Order 2: Being prepared
    curbside.put_item(Item={
        'orderId': 'CURB-20260127-002',
        'memberId': 'MEM-200045',
        'memberName': 'Michael Torres',
        'orderDate': today.strftime('%Y-%m-%d'),
        'orderTime': '13:30:00',
        'status': 'Being Prepared',
        'pickupInstructions': 'Park in designated curbside spots 1-10. Call when you arrive.',
        'items': [
            {'sku': 'ELEC-98765', 'name': 'Samsung 65" 4K Smart TV', 'quantity': 1}
        ],
        'total': Decimal('799.99'),
        'estimatedPickupTime': '4:00 PM - 6:00 PM',
        'readyTime': None
    })

    # Order 3: Scheduled for tomorrow
    curbside.put_item(Item={
        'orderId': 'CURB-20260128-001',
        'memberId': 'MEM-300123',
        'memberName': 'Jennifer Walsh',
        'orderDate': tomorrow,
        'orderTime': '08:00:00',
        'status': 'Scheduled',
        'pickupInstructions': 'Park in designated curbside spots 1-10. Call when you arrive.',
        'items': [
            {'sku': 'TIRE-11111', 'name': 'Michelin Tire 225/65R17', 'quantity': 4}
        ],
        'total': Decimal('759.96'),
        'estimatedPickupTime': '10:00 AM - 12:00 PM',
        'readyTime': None
    })

    print("Curbside orders seeded: 3 orders")

    # --- 6. Seed Appointments ---
    print("\n--- Seeding Appointments ---")
    appointments = dynamodb.Table('CallCenter_Appointments')

    # Appointment 1: Tire installation today
    appointments.put_item(Item={
        'appointmentId': 'APPT-TIRE-20260127-001',
        'memberId': 'MEM-100001',
        'memberName': 'Sarah Chen',
        'department': 'TireCenter',
        'serviceType': 'Tire Installation',
        'appointmentDate': today.strftime('%Y-%m-%d'),
        'appointmentTime': '3:00 PM',
        'duration': '1 hour',
        'status': 'Confirmed',
        'notes': '4 new tires - Michelin Defender',
        'confirmationNumber': 'TIRE-54321'
    })

    # Appointment 2: Eye exam next week
    next_week = (today + datetime.timedelta(days=7)).strftime('%Y-%m-%d')
    appointments.put_item(Item={
        'appointmentId': 'APPT-OPT-20260203-001',
        'memberId': 'MEM-200045',
        'memberName': 'Michael Torres',
        'department': 'OpticalCenter',
        'serviceType': 'Eye Exam',
        'appointmentDate': next_week,
        'appointmentTime': '10:00 AM',
        'duration': '45 minutes',
        'status': 'Confirmed',
        'notes': 'Annual checkup',
        'confirmationNumber': 'OPT-12345'
    })

    # Appointment 3: Prescription pickup ready
    appointments.put_item(Item={
        'appointmentId': 'APPT-PHRM-20260127-001',
        'memberId': 'MEM-300123',
        'memberName': 'Jennifer Walsh',
        'department': 'Pharmacy',
        'serviceType': 'Prescription Pickup',
        'appointmentDate': today.strftime('%Y-%m-%d'),
        'appointmentTime': 'Any time',
        'duration': 'N/A',
        'status': 'Ready',
        'notes': 'Prescription #RX-98765 filled and ready',
        'confirmationNumber': 'PHRM-67890'
    })

    print("Appointments seeded: 3 appointments")

    # --- 7. Seed Specialty Orders (Cakes) ---
    print("\n--- Seeding Specialty Orders ---")
    specialty = dynamodb.Table('CallCenter_Specialty_Orders')

    pickup_tomorrow = (today + datetime.timedelta(days=1)).strftime('%Y-%m-%d')

    # Cake order 1: Ready for pickup tomorrow
    specialty.put_item(Item={
        'orderId': 'CAKE-20260125-001',
        'memberId': 'MEM-100001',
        'memberName': 'Sarah Chen',
        'orderType': 'Cake',
        'orderDate': (today - datetime.timedelta(days=2)).strftime('%Y-%m-%d'),
        'pickupDate': pickup_tomorrow,
        'pickupTime': '2:00 PM',
        'status': 'Ready',
        'details': {
            'size': 'Half Sheet',
            'flavor': 'Chocolate with Vanilla Frosting',
            'inscription': 'Happy Birthday Emma!',
            'decorations': 'Pink and purple flowers, unicorn theme'
        },
        'price': Decimal('34.99'),
        'confirmationNumber': 'CAKE-78901'
    })

    # Cake order 2: In progress
    specialty.put_item(Item={
        'orderId': 'CAKE-20260126-001',
        'memberId': 'MEM-200045',
        'memberName': 'Michael Torres',
        'orderType': 'Cake',
        'orderDate': (today - datetime.timedelta(days=1)).strftime('%Y-%m-%d'),
        'pickupDate': (today + datetime.timedelta(days=2)).strftime('%Y-%m-%d'),
        'pickupTime': '5:00 PM',
        'status': 'In Progress',
        'details': {
            'size': 'Quarter Sheet',
            'flavor': 'Vanilla with Buttercream',
            'inscription': 'Congratulations Team!',
            'decorations': 'Company colors - blue and white'
        },
        'price': Decimal('24.99'),
        'confirmationNumber': 'CAKE-78902'
    })

    print("Specialty orders seeded: 2 cake orders")

    # --- 8. Seed Members ---
    print("\n--- Seeding Members ---")
    members = dynamodb.Table('CallCenter_Members')

    members.put_item(Item={
        'memberId': 'MEM-100001',
        'name': 'Sarah Chen',
        'phone': '+1-555-234-5678',
        'email': 'sarah.chen@example.com',
        'membershipType': 'Pro'
    })

    members.put_item(Item={
        'memberId': 'MEM-200045',
        'name': 'Michael Torres',
        'phone': '+1-555-876-5432',
        'email': 'mtorres@smallbiz.com',
        'membershipType': 'Business'
    })

    members.put_item(Item={
        'memberId': 'MEM-300123',
        'name': 'Jennifer Walsh',
        'phone': '+1-555-321-9876',
        'email': 'jwalsh@email.com',
        'membershipType': 'Consumer'
    })

    print("Members seeded: 3 members")

    print("\n--- Call Center Database Setup Complete ---")
    print("\nTest Scenarios:")
    print("1. Store Hours: Ask about hours for today, holidays, or specific departments")
    print("2. Inventory Check: Ask about 'Samsung TV' (in stock) or 'Dyson Vacuum' (out of stock)")
    print("3. Curbside Order: Member MEM-100001 order CURB-20260127-001 (ready)")
    print("4. Schedule Appointment: Book Tire Center, Optical, Hearing, or Pharmacy appointment")
    print("5. Cake Order: Member MEM-100001 has cake CAKE-78901 ready tomorrow")

if __name__ == '__main__':
    setup_call_center_demo_data()
