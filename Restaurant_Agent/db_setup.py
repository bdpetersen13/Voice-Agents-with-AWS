import boto3
import datetime
import time
from decimal import Decimal

def setup_restaurant_demo_data():
    """
    Sets up DynamoDB tables for a restaurant voice agent.
    Creates tables for: Reservations, Waitlist, Tables, Customers, Orders, Menu, Notifications
    """
    # Initialize DynamoDB resource
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

    # --- 1. Define Table Schemas ---
    tables = {
        'Restaurant_Reservations': {
            'KeySchema': [{'AttributeName': 'reservationId', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'reservationId', 'AttributeType': 'S'}]
        },
        'Restaurant_Waitlist': {
            'KeySchema': [{'AttributeName': 'waitlistId', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'waitlistId', 'AttributeType': 'S'}]
        },
        'Restaurant_Tables': {
            'KeySchema': [{'AttributeName': 'tableId', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'tableId', 'AttributeType': 'S'}]
        },
        'Restaurant_Customers': {
            'KeySchema': [{'AttributeName': 'customerId', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'customerId', 'AttributeType': 'S'}]
        },
        'Restaurant_Orders': {
            'KeySchema': [{'AttributeName': 'orderId', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'orderId', 'AttributeType': 'S'}]
        },
        'Restaurant_Menu': {
            'KeySchema': [{'AttributeName': 'itemId', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'itemId', 'AttributeType': 'S'}]
        },
        'Restaurant_Notifications': {
            'KeySchema': [{'AttributeName': 'notificationId', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'notificationId', 'AttributeType': 'S'}]
        }
    }

    # --- 2. Delete Old Tables & Create New Ones ---
    print("--- Resetting Restaurant Database ---")
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

    # --- 3. Seed Tables (Restaurant Table Inventory) ---
    print("\n--- Seeding Table Inventory ---")
    tables_table = dynamodb.Table('Restaurant_Tables')

    # Mix of table types with different capacities and features
    restaurant_tables = [
        # 2-person tables
        {'tableId': 'T-101', 'capacity': 2, 'location': 'Window', 'hasHighChair': False, 'isAccessible': False, 'status': 'Available'},
        {'tableId': 'T-102', 'capacity': 2, 'location': 'Window', 'hasHighChair': True, 'isAccessible': False, 'status': 'Available'},
        {'tableId': 'T-103', 'capacity': 2, 'location': 'Main Dining', 'hasHighChair': False, 'isAccessible': True, 'status': 'Available'},

        # 4-person tables
        {'tableId': 'T-201', 'capacity': 4, 'location': 'Window', 'hasHighChair': True, 'isAccessible': False, 'status': 'Available'},
        {'tableId': 'T-202', 'capacity': 4, 'location': 'Main Dining', 'hasHighChair': True, 'isAccessible': False, 'status': 'Available'},
        {'tableId': 'T-203', 'capacity': 4, 'location': 'Main Dining', 'hasHighChair': False, 'isAccessible': True, 'status': 'Available'},
        {'tableId': 'T-204', 'capacity': 4, 'location': 'Patio', 'hasHighChair': False, 'isAccessible': False, 'status': 'Available'},
        {'tableId': 'T-205', 'capacity': 4, 'location': 'Patio', 'hasHighChair': True, 'isAccessible': False, 'status': 'Available'},

        # 6-person tables
        {'tableId': 'T-301', 'capacity': 6, 'location': 'Main Dining', 'hasHighChair': True, 'isAccessible': False, 'status': 'Available'},
        {'tableId': 'T-302', 'capacity': 6, 'location': 'Main Dining', 'hasHighChair': True, 'isAccessible': True, 'status': 'Available'},

        # 8-person tables (large parties)
        {'tableId': 'T-401', 'capacity': 8, 'location': 'Private Room', 'hasHighChair': True, 'isAccessible': True, 'status': 'Available'},
        {'tableId': 'T-402', 'capacity': 8, 'location': 'Main Dining', 'hasHighChair': False, 'isAccessible': False, 'status': 'Available'},
    ]

    for table in restaurant_tables:
        tables_table.put_item(Item=table)

    print(f"Table inventory seeded: {len(restaurant_tables)} tables")

    # --- 4. Seed Customers ---
    print("\n--- Seeding Customers ---")
    customers = dynamodb.Table('Restaurant_Customers')

    today = datetime.date.today()

    customer_data = [
        {
            'customerId': 'CUST-10001',
            'name': 'Emily Rodriguez',
            'phone': '+1-555-123-4567',
            'email': 'emily.rodriguez@example.com',
            'vipStatus': True,
            'allergies': ['Peanuts', 'Shellfish'],
            'preferences': 'Window seating',
            'visitCount': 15
        },
        {
            'customerId': 'CUST-10002',
            'name': 'James Chen',
            'phone': '+1-555-234-5678',
            'email': 'james.chen@example.com',
            'vipStatus': False,
            'allergies': [],
            'preferences': 'Quiet area',
            'visitCount': 3
        },
        {
            'customerId': 'CUST-10003',
            'name': 'Sarah Williams',
            'phone': '+1-555-345-6789',
            'email': 'sarah.w@example.com',
            'vipStatus': True,
            'allergies': ['Gluten'],
            'preferences': 'Patio when available',
            'visitCount': 22
        },
        {
            'customerId': 'CUST-10004',
            'name': 'Michael Thompson',
            'phone': '+1-555-456-7890',
            'email': 'mthompson@example.com',
            'vipStatus': False,
            'allergies': [],
            'preferences': None,
            'visitCount': 1
        },
    ]

    for customer in customer_data:
        customers.put_item(Item=customer)

    print(f"Customers seeded: {len(customer_data)} customers")

    # --- 5. Seed Reservations ---
    print("\n--- Seeding Reservations ---")
    reservations = dynamodb.Table('Restaurant_Reservations')

    # Reservation 1: Tonight at 7 PM (confirmed)
    tonight_7pm = datetime.datetime.combine(today, datetime.time(19, 0))
    reservations.put_item(Item={
        'reservationId': 'RES-20260127-001',
        'customerId': 'CUST-10001',
        'customerName': 'Emily Rodriguez',
        'phone': '+1-555-123-4567',
        'partySize': 4,
        'reservationDate': today.strftime('%Y-%m-%d'),
        'reservationTime': '7:00 PM',
        'reservationDateTime': tonight_7pm.isoformat(),
        'tableId': 'T-201',
        'status': 'Confirmed',
        'specialRequests': 'Window seating, celebrating anniversary',
        'highChairNeeded': False,
        'accessibilityNeeded': False,
        'seatingPreference': 'Window',
        'createdAt': (datetime.datetime.now() - datetime.timedelta(days=3)).isoformat(),
        'notificationSent': False
    })

    # Reservation 2: Tonight at 8 PM (confirmed, has arrived and seated)
    tonight_8pm = datetime.datetime.combine(today, datetime.time(20, 0))
    reservations.put_item(Item={
        'reservationId': 'RES-20260127-002',
        'customerId': 'CUST-10003',
        'customerName': 'Sarah Williams',
        'phone': '+1-555-345-6789',
        'partySize': 2,
        'reservationDate': today.strftime('%Y-%m-%d'),
        'reservationTime': '8:00 PM',
        'reservationDateTime': tonight_8pm.isoformat(),
        'tableId': 'T-204',
        'status': 'Seated',
        'specialRequests': 'Gluten-free menu needed',
        'highChairNeeded': False,
        'accessibilityNeeded': False,
        'seatingPreference': 'Patio',
        'createdAt': (datetime.datetime.now() - datetime.timedelta(days=5)).isoformat(),
        'notificationSent': False,
        'seatedAt': (datetime.datetime.now() - datetime.timedelta(minutes=15)).isoformat()
    })

    # Reservation 3: Tomorrow at 6:30 PM (confirmed)
    tomorrow = today + datetime.timedelta(days=1)
    tomorrow_630pm = datetime.datetime.combine(tomorrow, datetime.time(18, 30))
    reservations.put_item(Item={
        'reservationId': 'RES-20260128-001',
        'customerId': 'CUST-10002',
        'customerName': 'James Chen',
        'phone': '+1-555-234-5678',
        'partySize': 6,
        'reservationDate': tomorrow.strftime('%Y-%m-%d'),
        'reservationTime': '6:30 PM',
        'reservationDateTime': tomorrow_630pm.isoformat(),
        'tableId': 'T-301',
        'status': 'Confirmed',
        'specialRequests': 'Family dinner, need high chair',
        'highChairNeeded': True,
        'accessibilityNeeded': False,
        'seatingPreference': 'Main Dining',
        'createdAt': datetime.datetime.now().isoformat(),
        'notificationSent': False
    })

    # Reservation 4: Tonight at 6 PM (cancelled by customer)
    tonight_6pm = datetime.datetime.combine(today, datetime.time(18, 0))
    reservations.put_item(Item={
        'reservationId': 'RES-20260127-003',
        'customerId': 'CUST-10004',
        'customerName': 'Michael Thompson',
        'phone': '+1-555-456-7890',
        'partySize': 2,
        'reservationDate': today.strftime('%Y-%m-%d'),
        'reservationTime': '6:00 PM',
        'reservationDateTime': tonight_6pm.isoformat(),
        'tableId': None,
        'status': 'Cancelled',
        'specialRequests': None,
        'highChairNeeded': False,
        'accessibilityNeeded': False,
        'seatingPreference': None,
        'createdAt': (datetime.datetime.now() - datetime.timedelta(days=2)).isoformat(),
        'cancelledAt': (datetime.datetime.now() - datetime.timedelta(hours=4)).isoformat(),
        'notificationSent': False
    })

    print("Reservations seeded: 4 reservations")

    # --- 6. Seed Waitlist ---
    print("\n--- Seeding Waitlist ---")
    waitlist = dynamodb.Table('Restaurant_Waitlist')

    # Waitlist entry 1: Walk-in waiting for table (active)
    waitlist.put_item(Item={
        'waitlistId': 'WAIT-20260127-001',
        'customerId': None,
        'customerName': 'Jennifer Martinez',
        'phone': '+1-555-567-8901',
        'partySize': 4,
        'requestedDate': today.strftime('%Y-%m-%d'),
        'requestedTime': '7:00 PM',
        'type': 'Walk-in',  # Walk-in or Reservation Waitlist
        'status': 'Waiting',
        'estimatedWaitMinutes': 25,
        'quotedAt': (datetime.datetime.now() - datetime.timedelta(minutes=10)).isoformat(),
        'highChairNeeded': True,
        'accessibilityNeeded': False,
        'seatingPreference': 'Main Dining',
        'notificationSent': False
    })

    # Waitlist entry 2: Requested tomorrow 7 PM but it's fully booked
    tomorrow_7pm = datetime.datetime.combine(tomorrow, datetime.time(19, 0))
    waitlist.put_item(Item={
        'waitlistId': 'WAIT-20260128-001',
        'customerId': 'CUST-10004',
        'customerName': 'Michael Thompson',
        'phone': '+1-555-456-7890',
        'partySize': 2,
        'requestedDate': tomorrow.strftime('%Y-%m-%d'),
        'requestedTime': '7:00 PM',
        'requestedDateTime': tomorrow_7pm.isoformat(),
        'type': 'Reservation Waitlist',
        'status': 'Waiting',
        'estimatedWaitMinutes': None,  # Will notify if opening becomes available
        'quotedAt': datetime.datetime.now().isoformat(),
        'highChairNeeded': False,
        'accessibilityNeeded': False,
        'seatingPreference': 'Window',
        'notificationSent': False
    })

    print("Waitlist seeded: 2 entries")

    # --- 7. Seed Menu ---
    print("\n--- Seeding Menu ---")
    menu = dynamodb.Table('Restaurant_Menu')

    menu_items = [
        # Appetizers
        {'itemId': 'APP-001', 'category': 'Appetizer', 'name': 'Bruschetta', 'description': 'Grilled bread with tomatoes, basil, and mozzarella', 'price': Decimal('12.99'), 'available': True, 'allergens': ['Gluten', 'Dairy']},
        {'itemId': 'APP-002', 'category': 'Appetizer', 'name': 'Calamari Fritti', 'description': 'Crispy fried calamari with marinara', 'price': Decimal('14.99'), 'available': True, 'allergens': ['Shellfish', 'Gluten']},
        {'itemId': 'APP-003', 'category': 'Appetizer', 'name': 'Caesar Salad', 'description': 'Romaine, parmesan, croutons, Caesar dressing', 'price': Decimal('10.99'), 'available': True, 'allergens': ['Gluten', 'Dairy', 'Eggs']},

        # Entrees
        {'itemId': 'ENT-001', 'category': 'Entree', 'name': 'Margherita Pizza', 'description': 'Fresh mozzarella, basil, tomato sauce', 'price': Decimal('16.99'), 'available': True, 'allergens': ['Gluten', 'Dairy']},
        {'itemId': 'ENT-002', 'category': 'Entree', 'name': 'Fettuccine Alfredo', 'description': 'Creamy parmesan sauce with fettuccine', 'price': Decimal('18.99'), 'available': True, 'allergens': ['Gluten', 'Dairy']},
        {'itemId': 'ENT-003', 'category': 'Entree', 'name': 'Grilled Salmon', 'description': '8oz Atlantic salmon with vegetables', 'price': Decimal('26.99'), 'available': True, 'allergens': ['Fish']},
        {'itemId': 'ENT-004', 'category': 'Entree', 'name': 'Ribeye Steak', 'description': '12oz ribeye with mashed potatoes', 'price': Decimal('34.99'), 'available': True, 'allergens': []},
        {'itemId': 'ENT-005', 'category': 'Entree', 'name': 'Chicken Parmesan', 'description': 'Breaded chicken with marinara and mozzarella', 'price': Decimal('22.99'), 'available': False, 'allergens': ['Gluten', 'Dairy']},  # Out of stock

        # Desserts
        {'itemId': 'DES-001', 'category': 'Dessert', 'name': 'Tiramisu', 'description': 'Classic Italian coffee-flavored dessert', 'price': Decimal('8.99'), 'available': True, 'allergens': ['Gluten', 'Dairy', 'Eggs']},
        {'itemId': 'DES-002', 'category': 'Dessert', 'name': 'Chocolate Lava Cake', 'description': 'Warm chocolate cake with vanilla ice cream', 'price': Decimal('9.99'), 'available': True, 'allergens': ['Gluten', 'Dairy', 'Eggs']},

        # Beverages
        {'itemId': 'BEV-001', 'category': 'Beverage', 'name': 'House Red Wine', 'description': 'Glass of house Cabernet', 'price': Decimal('9.00'), 'available': True, 'allergens': []},
        {'itemId': 'BEV-002', 'category': 'Beverage', 'name': 'San Pellegrino', 'description': 'Sparkling mineral water', 'price': Decimal('4.50'), 'available': True, 'allergens': []},
    ]

    for item in menu_items:
        menu.put_item(Item=item)

    print(f"Menu seeded: {len(menu_items)} items")

    # --- 8. Seed Orders (for seated guests) ---
    print("\n--- Seeding Orders ---")
    orders = dynamodb.Table('Restaurant_Orders')

    # Order for Sarah Williams (RES-20260127-002, currently seated)
    orders.put_item(Item={
        'orderId': 'ORD-20260127-001',
        'reservationId': 'RES-20260127-002',
        'customerId': 'CUST-10003',
        'customerName': 'Sarah Williams',
        'tableId': 'T-204',
        'orderDate': today.strftime('%Y-%m-%d'),
        'orderTime': (datetime.datetime.now() - datetime.timedelta(minutes=10)).isoformat(),
        'items': [
            {'itemId': 'APP-003', 'name': 'Caesar Salad', 'quantity': 1, 'price': Decimal('10.99'), 'specialInstructions': 'No croutons (gluten-free)'},
            {'itemId': 'ENT-003', 'name': 'Grilled Salmon', 'quantity': 1, 'price': Decimal('26.99'), 'specialInstructions': None},
            {'itemId': 'BEV-001', 'name': 'House Red Wine', 'quantity': 2, 'price': Decimal('9.00'), 'specialInstructions': None}
        ],
        'subtotal': Decimal('55.98'),
        'tax': Decimal('5.60'),
        'total': Decimal('61.58'),
        'status': 'In Progress',
        'specialRequests': 'Gluten-free preparation'
    })

    print("Orders seeded: 1 active order")

    # --- 9. Seed Notifications ---
    print("\n--- Seeding Notifications ---")
    notifications = dynamodb.Table('Restaurant_Notifications')

    # Pending notification for waitlist customer
    notifications.put_item(Item={
        'notificationId': 'NOTIF-20260127-001',
        'waitlistId': 'WAIT-20260127-001',
        'phone': '+1-555-567-8901',
        'customerName': 'Jennifer Martinez',
        'message': 'Your table for 4 is ready! Please come to the host stand.',
        'status': 'Pending',
        'createdAt': datetime.datetime.now().isoformat(),
        'sentAt': None
    })

    print("Notifications seeded: 1 pending notification")

    print("\n--- Restaurant Database Setup Complete ---")
    print("\nTest Scenarios:")
    print("1. Reservation Lookup: Use phone +1-555-123-4567 (Emily Rodriguez) or +1-555-345-6789 (Sarah Williams)")
    print("2. Create Reservation: Book for tomorrow evening")
    print("3. Edit Reservation: Modify party size or time for RES-20260128-001")
    print("4. Cancel Reservation: Cancel RES-20260127-001")
    print("5. Join Waitlist: Request fully booked time slot")
    print("6. Place Order: Sarah Williams (RES-20260127-002) is seated at T-204")
    print("7. Check Wait Time: Current walk-in wait is ~25 minutes for party of 4")
    print("8. No Reservation Name: Use phone number +1-555-234-5678 to lookup James Chen")

if __name__ == '__main__':
    setup_restaurant_demo_data()
