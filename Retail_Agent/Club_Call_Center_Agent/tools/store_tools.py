"""
Store Tools
Tools for store hours and inventory checks
"""
import datetime
from typing import Dict, Any
from boto3.dynamodb.conditions import Attr
from tools.base_tool import BaseTool


class CheckStoreHoursTool(BaseTool):
    """Check store hours - regular, holiday, department-specific, or special closures"""

    def __init__(self, dynamodb, store_info_table):
        super().__init__(dynamodb)
        self.store_info_table = store_info_table

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check store hours - regular, holiday, department-specific, or today's hours.
        """
        try:
            store_id = content_data.get("storeId", "STORE-4523")  # Default to main store
            query_type = content_data.get("queryType", "regular")  # regular, holiday, department, today
            department = content_data.get("department")  # TireCenter, OpticalCenter, etc.
            specific_date = content_data.get("date")  # For checking specific dates

            response = self.store_info_table.get_item(Key={'storeId': store_id})

            if 'Item' not in response:
                return {"error": "Store information not found."}

            store = response['Item']

            # Determine today's day of week
            today = datetime.date.today()
            day_name = today.strftime('%A')

            # Query type: TODAY
            if query_type == "today" or not query_type:
                regular_hours = store.get('regularHours', {})
                today_hours = regular_hours.get(day_name, 'Not available')

                return {
                    "storeId": store_id,
                    "storeName": store.get('storeName'),
                    "today": day_name,
                    "hours": today_hours,
                    "message": f"Today ({day_name}), we're open {today_hours}."
                }

            # Query type: REGULAR
            elif query_type == "regular":
                regular_hours = store.get('regularHours', {})
                return {
                    "storeId": store_id,
                    "storeName": store.get('storeName'),
                    "regularHours": regular_hours,
                    "message": "Our regular hours are: " + ", ".join([f"{day}: {hours}" for day, hours in regular_hours.items()])
                }

            # Query type: HOLIDAY
            elif query_type == "holiday":
                holiday_hours = store.get('holidayHours', {})
                return {
                    "storeId": store_id,
                    "storeName": store.get('storeName'),
                    "holidayHours": holiday_hours,
                    "message": "Our holiday hours are: " + ", ".join([f"{holiday}: {hours}" for holiday, hours in holiday_hours.items()])
                }

            # Query type: DEPARTMENT
            elif query_type == "department" and department:
                departments = store.get('departments', {})
                dept_info = departments.get(department)

                if not dept_info:
                    return {"error": f"Department {department} not found."}

                return {
                    "storeId": store_id,
                    "department": department,
                    "hours": dept_info.get('hours'),
                    "phone": dept_info.get('phone'),
                    "appointmentsAvailable": dept_info.get('appointmentsAvailable', False),
                    "message": f"{department} hours: {dept_info.get('hours')}. Phone: {dept_info.get('phone')}"
                }

            else:
                return {"error": "Invalid query type or missing parameters."}

        except Exception as e:
            return {"error": str(e)}


class CheckInventoryTool(BaseTool):
    """Check if an item is in stock, get aisle location, and price"""

    def __init__(self, dynamodb, inventory_table):
        super().__init__(dynamodb)
        self.inventory_table = inventory_table

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if an item is in stock, get aisle location, and price.
        Supports search by SKU or product name.
        """
        try:
            sku = content_data.get("sku")
            product_name = content_data.get("productName")

            if not sku and not product_name:
                return {"error": "Either SKU or product name is required."}

            # Direct SKU lookup
            if sku:
                response = self.inventory_table.get_item(Key={'sku': sku})
                if 'Item' in response:
                    item = self.convert_decimals(response['Item'])
                    in_stock = item.get('inStock', False)
                    quantity = item.get('quantity', 0)

                    if in_stock and quantity > 0:
                        return {
                            "found": True,
                            "inStock": True,
                            "product": item,
                            "message": f"{item['productName']} is in stock! We have {quantity} available in {item['aisleLocation']}. Price: ${item['price']}"
                        }
                    else:
                        expected_restock = item.get('expectedRestock')
                        restock_msg = f" Expected restock: {expected_restock}" if expected_restock else ""
                        return {
                            "found": True,
                            "inStock": False,
                            "product": item,
                            "message": f"{item['productName']} is currently out of stock.{restock_msg}"
                        }

            # Search by product name (partial match)
            if product_name:
                response = self.inventory_table.scan(
                    FilterExpression=Attr('productName').contains(product_name)
                )

                items = response.get('Items', [])
                if not items:
                    return {
                        "found": False,
                        "message": f"No products found matching '{product_name}'. Can you provide more details or the SKU?"
                    }

                # Return first match
                item = self.convert_decimals(items[0])
                in_stock = item.get('inStock', False)
                quantity = item.get('quantity', 0)

                if in_stock and quantity > 0:
                    return {
                        "found": True,
                        "inStock": True,
                        "product": item,
                        "message": f"{item['productName']} is in stock! We have {quantity} available in {item['aisleLocation']}. Price: ${item['price']}"
                    }
                else:
                    expected_restock = item.get('expectedRestock')
                    restock_msg = f" Expected restock: {expected_restock}" if expected_restock else ""
                    return {
                        "found": True,
                        "inStock": False,
                        "product": item,
                        "message": f"{item['productName']} is currently out of stock.{restock_msg}"
                    }

            return {"found": False, "message": "Item not found."}

        except Exception as e:
            return {"error": str(e)}
