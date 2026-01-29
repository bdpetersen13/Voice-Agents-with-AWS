"""
Menu Tools
Tools for viewing restaurant menu
"""
from typing import Dict, Any
from boto3.dynamodb.conditions import Attr
from tools.base_tool import BaseTool
from config.constants import TABLE_MENU


class ViewMenuTool(BaseTool):
    """
    View menu items by category or show all available items.
    """

    def __init__(self, dynamodb):
        super().__init__(dynamodb)
        self.menu_table = dynamodb.Table(TABLE_MENU)

    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            category = content_data.get("category")  # Appetizer, Entree, Dessert, Beverage

            # Scan menu
            if category:
                response = self.menu_table.scan(
                    FilterExpression=Attr('category').eq(category) & Attr('available').eq(True)
                )
            else:
                response = self.menu_table.scan(FilterExpression=Attr('available').eq(True))

            items = response.get('Items', [])
            items = self.convert_decimals(items)

            # Group by category
            by_category = {}
            for item in items:
                cat = item.get('category', 'Other')
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(item)

            return {
                "itemCount": len(items),
                "categories": by_category,
                "requestedCategory": category,
                "message": f"Found {len(items)} available menu items" + (f" in {category}" if category else ".")
            }

        except Exception as e:
            return {"error": str(e)}
