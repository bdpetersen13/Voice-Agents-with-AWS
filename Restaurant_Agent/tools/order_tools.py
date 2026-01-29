"""
Order Tools
Tools for managing food orders
"""
import datetime
import random
from typing import Dict, Any
from decimal import Decimal
from boto3.dynamodb.conditions import Attr
from tools.base_tool import BaseTool
from config.constants import TABLE_RESERVATIONS, TABLE_ORDERS, TABLE_MENU, ORDER_ID_PREFIX, TAX_RATE


class PlaceOrderTool(BaseTool):
    """
    Place food order for seated guest.
    """

    def __init__(self, dynamodb):
        super().__init__(dynamodb)
        self.reservations_table = dynamodb.Table(TABLE_RESERVATIONS)
        self.orders_table = dynamodb.Table(TABLE_ORDERS)
        self.menu_table = dynamodb.Table(TABLE_MENU)

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            reservation_id = content_data.get("reservationId")
            customer_name = content_data.get("customerName")
            table_id = content_data.get("tableId")
            items = content_data.get("items")  # List of {itemId, quantity, specialInstructions}

            if not items:
                return {"error": "items list is required to place an order."}

            # Get reservation if provided
            customer_id = None
            if reservation_id:
                response = self.reservations_table.get_item(Key={'reservationId': reservation_id})
                if 'Item' in response:
                    customer_id = response['Item'].get('customerId')
                    customer_name = response['Item'].get('customerName')
                    table_id = response['Item'].get('tableId')

            # Calculate total
            subtotal = Decimal('0.00')
            order_items = []

            for item_request in items:
                item_id = item_request.get('itemId')
                quantity = item_request.get('quantity', 1)
                special_instructions = item_request.get('specialInstructions')

                # Lookup menu item
                menu_response = self.menu_table.get_item(Key={'itemId': item_id})
                if 'Item' not in menu_response:
                    return {"error": f"Menu item {item_id} not found."}

                menu_item = menu_response['Item']

                if not menu_item.get('available', False):
                    return {"error": f"{menu_item['name']} is currently unavailable."}

                item_price = menu_item['price']
                item_total = item_price * quantity
                subtotal += item_total

                order_items.append({
                    'itemId': item_id,
                    'name': menu_item['name'],
                    'quantity': quantity,
                    'price': item_price,
                    'specialInstructions': special_instructions
                })

            # Calculate tax
            tax = (subtotal * Decimal(str(TAX_RATE))).quantize(Decimal('0.01'))
            total = subtotal + tax

            # Create order
            order_id = f"{ORDER_ID_PREFIX}-{datetime.datetime.now().strftime('%Y%m%d')}-{random.randint(100, 999):03d}"

            order = {
                'orderId': order_id,
                'reservationId': reservation_id,
                'customerId': customer_id,
                'customerName': customer_name,
                'tableId': table_id,
                'orderDate': datetime.date.today().strftime('%Y-%m-%d'),
                'orderTime': datetime.datetime.now().isoformat(),
                'items': order_items,
                'subtotal': subtotal,
                'tax': tax,
                'total': total,
                'status': 'In Progress',
                'specialRequests': content_data.get('specialRequests')
            }

            self.orders_table.put_item(Item=order)

            return {
                "success": True,
                "orderId": order_id,
                "subtotal": str(subtotal),
                "tax": str(tax),
                "total": str(total),
                "itemCount": len(order_items),
                "message": f"Order {order_id} placed successfully. Total: ${total}. Your food will be out shortly!"
            }

        except Exception as e:
            return {"error": str(e)}


class CheckOrderStatusTool(BaseTool):
    """
    Check status of an order.
    """

    def __init__(self, dynamodb):
        super().__init__(dynamodb)
        self.orders_table = dynamodb.Table(TABLE_ORDERS)

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            order_id = content_data.get("orderId")
            table_id = content_data.get("tableId")

            if not order_id and not table_id:
                return {"error": "Either orderId or tableId is required."}

            if order_id:
                response = self.orders_table.get_item(Key={'orderId': order_id})
                if 'Item' not in response:
                    return {"found": False, "message": "Order not found."}
                order = self.convert_decimals(response['Item'])
            else:
                # Lookup by table
                response = self.orders_table.scan(FilterExpression=Attr('tableId').eq(table_id))
                orders = response.get('Items', [])
                if not orders:
                    return {"found": False, "message": "No orders found for this table."}
                order = self.convert_decimals(orders[0])

            return {
                "found": True,
                "order": order,
                "message": f"Order {order['orderId']} status: {order.get('status')}. Total: ${order.get('total')}."
            }

        except Exception as e:
            return {"error": str(e)}
