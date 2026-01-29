import boto3
import datetime
import time
from decimal import Decimal

def setup_retail_demo_data():
    """
    Sets up DynamoDB tables for a retail member service kiosk agent.
    Creates tables for: Members, Transactions, Returns, Service_Requests
    """
    # Initialize DynamoDB resource
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

    # --- 1. Define Table Schemas ---
    tables = {
        'Retail_Members': {
            'KeySchema': [{'AttributeName': 'memberId', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'memberId', 'AttributeType': 'S'}]
        },
        'Retail_Transactions': {
            'KeySchema': [{'AttributeName': 'transactionId', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'transactionId', 'AttributeType': 'S'}]
        },
        'Retail_Returns': {
            'KeySchema': [{'AttributeName': 'returnId', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'returnId', 'AttributeType': 'S'}]
        },
        'Retail_Service_Requests': {
            'KeySchema': [{'AttributeName': 'requestId', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'requestId', 'AttributeType': 'S'}]
        }
    }

    # --- 2. Delete Old Tables & Create New Ones ---
    print("--- Resetting Retail Member Service Database ---")
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

    # --- 3. Seed Member Data ---
    print("\n--- Seeding Retail Members ---")
    members = dynamodb.Table('Retail_Members')

    # Member 1: Pro member with household member
    members.put_item(Item={
        'memberId': 'MEM-100001',
        'membershipType': 'Pro',
        'membershipStatus': 'Active',
        'membershipStartDate': '2023-03-15',
        'membershipRenewalDate': '2027-03-15',
        'primaryMember': {
            'name': 'Sarah Chen',
            'dob': '1988-07-22',
            'phone': '+1-555-234-5678',
            'email': 'sarah.chen@example.com',
            'address': '1234 Maple Street, Denver, CO 80202'
        },
        'householdMembers': [
            {
                'name': 'David Chen',
                'dob': '1986-04-10',
                'relationship': 'Spouse'
            }
        ],
        'paymentMethod': {
            'type': 'Visa',
            'last4': '4532',
            'expiryDate': '08/28'
        },
        'rewardsBalance': Decimal('187.50'),
        'loyaltyPoints': 3200
    })

    # Member 2: Business member, no household member
    members.put_item(Item={
        'memberId': 'MEM-200045',
        'membershipType': 'Business',
        'membershipStatus': 'Active',
        'membershipStartDate': '2022-01-10',
        'membershipRenewalDate': '2027-01-10',
        'primaryMember': {
            'name': 'Michael Torres',
            'dob': '1975-11-03',
            'phone': '+1-555-876-5432',
            'email': 'mtorres@smallbiz.com',
            'address': '5678 Business Park Dr, Denver, CO 80203'
        },
        'householdMembers': [],
        'paymentMethod': {
            'type': 'AmEx',
            'last4': '9876',
            'expiryDate': '12/26'
        },
        'rewardsBalance': Decimal('425.00'),
        'loyaltyPoints': 8500
    })

    # Member 3: Consumer member with issue today
    members.put_item(Item={
        'memberId': 'MEM-300123',
        'membershipType': 'Consumer',
        'membershipStatus': 'Active',
        'membershipStartDate': '2024-06-01',
        'membershipRenewalDate': '2026-06-01',
        'primaryMember': {
            'name': 'Jennifer Walsh',
            'dob': '1992-02-18',
            'phone': '+1-555-321-9876',
            'email': 'jwalsh@email.com',
            'address': '9012 Oak Lane, Denver, CO 80204'
        },
        'householdMembers': [],
        'paymentMethod': {
            'type': 'MasterCard',
            'last4': '1234',
            'expiryDate': '03/27'
        },
        'rewardsBalance': Decimal('0.00'),
        'loyaltyPoints': 450
    })

    print("Members seeded:")
    print(" - MEM-100001 (Sarah Chen, Pro)")
    print(" - MEM-200045 (Michael Torres, Business)")
    print(" - MEM-300123 (Jennifer Walsh, Consumer)")

    # --- 4. Seed Transaction Data ---
    print("\n--- Seeding Retail Transactions ---")
    transactions = dynamodb.Table('Retail_Transactions')

    today = datetime.date.today()
    yesterday = (today - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    week_ago = (today - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
    today_str = today.strftime('%Y-%m-%d')

    # Transaction 1: Sarah's recent purchase (returnable item)
    transactions.put_item(Item={
        'transactionId': 'TXN-20260120-001234',
        'memberId': 'MEM-100001',
        'date': week_ago,
        'time': '15:42:18',
        'location': 'Store #4523 - Denver, CO',
        'registerNum': 'Reg3',
        'items': [
            {
                'sku': 'ELEC-12345',
                'name': 'Wireless Headphones',
                'quantity': 1,
                'unitPrice': Decimal('79.99'),
                'totalPrice': Decimal('79.99'),
                'returnable': True,
                'weight': Decimal('0.45')  # kg
            },
            {
                'sku': 'GROC-98765',
                'name': 'Organic Coffee Beans 2lb',
                'quantity': 2,
                'unitPrice': Decimal('14.99'),
                'totalPrice': Decimal('29.98'),
                'returnable': True,
                'weight': Decimal('0.91')  # kg per unit
            },
            {
                'sku': 'HOME-55555',
                'name': 'Bath Towel Set',
                'quantity': 1,
                'unitPrice': Decimal('34.99'),
                'totalPrice': Decimal('34.99'),
                'returnable': True,
                'weight': Decimal('1.2')  # kg
            }
        ],
        'subtotal': Decimal('144.96'),
        'tax': Decimal('11.60'),
        'total': Decimal('156.56'),
        'paymentMethod': 'Visa ending in 4532',
        'cashier': 'Associate #12345'
    })

    # Transaction 2: Michael's bulk business purchase
    transactions.put_item(Item={
        'transactionId': 'TXN-20260115-005678',
        'memberId': 'MEM-200045',
        'date': (today - datetime.timedelta(days=12)).strftime('%Y-%m-%d'),
        'time': '10:15:32',
        'location': 'Store #4523 - Denver, CO',
        'registerNum': 'Reg7',
        'items': [
            {
                'sku': 'OFF-24680',
                'name': 'Copy Paper 10-Ream Case',
                'quantity': 3,
                'unitPrice': Decimal('45.99'),
                'totalPrice': Decimal('137.97'),
                'returnable': True,
                'weight': Decimal('22.5')  # kg per case
            },
            {
                'sku': 'OFF-13579',
                'name': 'Ballpoint Pens 50-Pack',
                'quantity': 5,
                'unitPrice': Decimal('12.99'),
                'totalPrice': Decimal('64.95'),
                'returnable': True,
                'weight': Decimal('0.6')  # kg per pack
            }
        ],
        'subtotal': Decimal('202.92'),
        'tax': Decimal('16.23'),
        'total': Decimal('219.15'),
        'paymentMethod': 'AmEx ending in 9876',
        'cashier': 'Associate #34567'
    })

    # Transaction 3: Jennifer's purchase TODAY with double-scan issue
    transactions.put_item(Item={
        'transactionId': f'TXN-{today_str.replace("-", "")}-009988',
        'memberId': 'MEM-300123',
        'date': today_str,
        'time': '14:23:45',
        'location': 'Store #4523 - Denver, CO',
        'registerNum': 'Reg5',
        'items': [
            {
                'sku': 'FOOD-11111',
                'name': 'Mixed Nuts 3lb Container',
                'quantity': 2,  # ISSUE: Should be 1, was double-scanned
                'unitPrice': Decimal('18.99'),
                'totalPrice': Decimal('37.98'),
                'returnable': True,
                'weight': Decimal('1.36')  # kg per container
            },
            {
                'sku': 'BAKE-22222',
                'name': 'Artisan Bread 2-Pack',
                'quantity': 1,
                'unitPrice': Decimal('6.99'),
                'totalPrice': Decimal('6.99'),
                'returnable': False,  # Perishable
                'weight': Decimal('0.8')  # kg
            }
        ],
        'subtotal': Decimal('44.97'),
        'tax': Decimal('3.60'),
        'total': Decimal('48.57'),
        'paymentMethod': 'MasterCard ending in 1234',
        'cashier': 'Associate #56789'
    })

    print("Transactions seeded:")
    print(" - TXN-20260120-001234 (Sarah, 7 days ago, has returnable items)")
    print(" - TXN-20260115-005678 (Michael, 12 days ago, bulk business order)")
    print(f" - TXN-{today_str.replace('-', '')}-009988 (Jennifer, TODAY, double-scan issue)")

    # --- 5. Seed Returns Data ---
    print("\n--- Seeding Returns Data ---")
    returns = dynamodb.Table('Retail_Returns')

    # Past return example for reference
    returns.put_item(Item={
        'returnId': 'RET-20260110-00001',
        'transactionId': 'TXN-20251220-001111',
        'memberId': 'MEM-100001',
        'returnDate': '2026-01-10',
        'returnedItems': [
            {
                'sku': 'HOME-33333',
                'name': 'Kitchen Blender',
                'quantity': 1,
                'refundAmount': Decimal('89.99'),
                'reason': 'Did not meet expectations'
            }
        ],
        'refundTotal': Decimal('89.99'),
        'refundMethod': 'Original payment method (Visa 4532)',
        'status': 'Processed'
    })

    print("Returns seeded:")
    print(" - RET-20260110-00001 (Sarah, past return processed)")

    # --- 6. Seed Service Requests ---
    print("\n--- Seeding Service Requests ---")
    requests = dynamodb.Table('Retail_Service_Requests')

    # Open complaint example
    requests.put_item(Item={
        'requestId': 'REQ-20260125-00123',
        'memberId': 'MEM-200045',
        'requestType': 'Complaint',
        'description': 'Long wait time at checkout during peak hours',
        'status': 'Open',
        'createdDate': '2026-01-25T16:30:00Z',
        'resolvedDate': None,
        'resolution': ''
    })

    print("Service Requests seeded:")
    print(" - REQ-20260125-00123 (Michael, open complaint)")

    print("\n--- Retail Member Service Database Setup Complete ---")
    print("\nTest Scenarios:")
    print("1. Return Flow: Use MEM-100001, return 'Wireless Headphones' from TXN-20260120-001234")
    print("2. Transaction Issue: Use MEM-300123, fix double-scan on today's transaction")
    print("3. Membership Modification: Use MEM-200045, update contact info or payment method")

if __name__ == '__main__':
    setup_retail_demo_data()
