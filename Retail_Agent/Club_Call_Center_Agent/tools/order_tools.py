"""
Order Tools
Tools for managing curbside orders, specialty orders, and cake orders
"""
import datetime
import random
from decimal import Decimal
from typing import Dict, Any
from boto3.dynamodb.conditions import Attr
from tools.base_tool import BaseTool


class CheckCurbsideOrderTool(BaseTool):
    """Check curbside order status by order ID or member ID"""

    def __init__(self, dynamodb, curbside_table):
        super().__init__(dynamodb)
        self.curbside_table = curbside_table

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check curbside order status by order ID or member ID.
        """
        try:
            order_id = content_data.get("orderId")
            member_id = content_data.get("memberId")

            if not order_id and not member_id:
                return {"error": "Either orderId or memberId is required."}

            # Direct order lookup
            if order_id:
                response = self.curbside_table.get_item(Key={'orderId': order_id})
                if 'Item' in response:
                    order = self.convert_decimals(response['Item'])
                    status = order.get('status')
                    ready_time = order.get('readyTime')

                    if status == 'Ready for Pickup':
                        return {
                            "found": True,
                            "order": order,
                            "message": f"Your order {order_id} is ready for pickup! {order.get('pickupInstructions')} Ready since: {ready_time}"
                        }
                    elif status == 'Being Prepared':
                        estimated = order.get('estimatedPickupTime')
                        return {
                            "found": True,
                            "order": order,
                            "message": f"Your order {order_id} is currently being prepared. Estimated ready time: {estimated}"
                        }
                    elif status == 'Scheduled':
                        pickup_date = order.get('orderDate')
                        estimated = order.get('estimatedPickupTime')
                        return {
                            "found": True,
                            "order": order,
                            "message": f"Your order {order_id} is scheduled for {pickup_date}. Estimated ready time: {estimated}"
                        }
                    else:
                        return {
                            "found": True,
                            "order": order,
                            "message": f"Your order {order_id} status: {status}"
                        }

            # Search by member ID - find most recent order
            if member_id:
                response = self.curbside_table.scan(
                    FilterExpression=Attr('memberId').eq(member_id)
                )

                items = response.get('Items', [])
                if not items:
                    return {"found": False, "message": "No curbside orders found for this member."}

                # Sort by order date (most recent first)
                items.sort(key=lambda x: x.get('orderDate', ''), reverse=True)
                order = self.convert_decimals(items[0])

                status = order.get('status')
                order_id = order.get('orderId')

                if status == 'Ready for Pickup':
                    return {
                        "found": True,
                        "order": order,
                        "message": f"Your most recent order {order_id} is ready for pickup! {order.get('pickupInstructions')}"
                    }
                else:
                    return {
                        "found": True,
                        "order": order,
                        "message": f"Your most recent order {order_id} status: {status}. Estimated ready time: {order.get('estimatedPickupTime')}"
                    }

            return {"found": False, "message": "Order not found."}

        except Exception as e:
            return {"error": str(e)}


class CheckSpecialtyOrderTool(BaseTool):
    """Check specialty order (cake, custom) status by order ID or member ID"""

    def __init__(self, dynamodb, specialty_table):
        super().__init__(dynamodb)
        self.specialty_table = specialty_table

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check specialty order (cake, custom) status by order ID or member ID.
        """
        try:
            order_id = content_data.get("orderId")
            member_id = content_data.get("memberId")
            order_type = content_data.get("orderType", "Cake")  # Default to cake

            if not order_id and not member_id:
                return {"error": "Either orderId or memberId is required."}

            # Direct order lookup
            if order_id:
                response = self.specialty_table.get_item(Key={'orderId': order_id})
                if 'Item' in response:
                    order = self.convert_decimals(response['Item'])
                    status = order.get('status')
                    pickup_date = order.get('pickupDate')
                    pickup_time = order.get('pickupTime')

                    if status == 'Ready':
                        return {
                            "found": True,
                            "order": order,
                            "message": f"Your {order_type} order {order_id} is ready for pickup on {pickup_date} at {pickup_time}!"
                        }
                    elif status == 'In Progress':
                        return {
                            "found": True,
                            "order": order,
                            "message": f"Your {order_type} order {order_id} is being prepared. Pickup scheduled for {pickup_date} at {pickup_time}."
                        }
                    else:
                        return {
                            "found": True,
                            "order": order,
                            "message": f"Your {order_type} order {order_id} status: {status}"
                        }

            # Search by member ID
            if member_id:
                response = self.specialty_table.scan(
                    FilterExpression=Attr('memberId').eq(member_id) & Attr('orderType').eq(order_type)
                )

                items = response.get('Items', [])
                if not items:
                    return {"found": False, "message": f"No {order_type} orders found for this member."}

                # Sort by pickup date (most recent first)
                items.sort(key=lambda x: x.get('pickupDate', ''), reverse=True)
                order = self.convert_decimals(items[0])

                status = order.get('status')
                pickup_date = order.get('pickupDate')
                order_id = order.get('orderId')

                return {
                    "found": True,
                    "order": order,
                    "message": f"Your most recent {order_type} order {order_id} status: {status}. Pickup: {pickup_date}"
                }

            return {"found": False, "message": "Order not found."}

        except Exception as e:
            return {"error": str(e)}


class CreateCakeOrderTool(BaseTool):
    """Create a new cake order (requires 48-hour lead time)"""

    def __init__(self, dynamodb, specialty_table):
        super().__init__(dynamodb)
        self.specialty_table = specialty_table

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new cake order.
        Requires 48-hour lead time.
        """
        try:
            member_id = content_data.get("memberId")
            member_name = content_data.get("memberName")
            size = content_data.get("size")  # Quarter Sheet, Half Sheet, Full Sheet
            flavor = content_data.get("flavor")
            inscription = content_data.get("inscription", "")
            decorations = content_data.get("decorations", "")
            pickup_date = content_data.get("pickupDate")
            pickup_time = content_data.get("pickupTime", "2:00 PM")

            if not all([member_id, size, flavor, pickup_date]):
                return {"error": "memberId, size, flavor, and pickupDate are required."}

            # Validate 48-hour lead time
            today = datetime.date.today()
            try:
                pickup = datetime.datetime.strptime(pickup_date, '%Y-%m-%d').date()
                days_until = (pickup - today).days

                if days_until < 2:
                    return {
                        "success": False,
                        "message": "Cake orders require a 48-hour lead time. Please choose a pickup date at least 2 days from today."
                    }
            except ValueError:
                return {"error": "Invalid pickup date format. Use YYYY-MM-DD."}

            # Generate order ID and confirmation
            order_id = f"CAKE-{today.strftime('%Y%m%d')}-{random.randint(100, 999)}"
            confirmation = f"CAKE-{random.randint(10000, 99999)}"

            # Calculate price based on size
            prices = {
                "Quarter Sheet": Decimal("24.99"),
                "Half Sheet": Decimal("34.99"),
                "Full Sheet": Decimal("54.99")
            }
            price = prices.get(size, Decimal("34.99"))

            # Create order
            self.specialty_table.put_item(Item={
                'orderId': order_id,
                'memberId': member_id,
                'memberName': member_name or "Member",
                'orderType': 'Cake',
                'orderDate': today.strftime('%Y-%m-%d'),
                'pickupDate': pickup_date,
                'pickupTime': pickup_time,
                'status': 'In Progress',
                'details': {
                    'size': size,
                    'flavor': flavor,
                    'inscription': inscription,
                    'decorations': decorations
                },
                'price': price,
                'confirmationNumber': confirmation
            })

            return {
                "success": True,
                "orderId": order_id,
                "confirmationNumber": confirmation,
                "price": str(price),
                "message": f"Cake order created successfully! {size} {flavor} cake ready for pickup on {pickup_date} at {pickup_time}. Your confirmation number is {confirmation}. Total: ${price}"
            }

        except Exception as e:
            return {"error": str(e)}
