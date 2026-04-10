from .order_tool import BaseTool

class InventoryTool(BaseTool):
    def __init__(self):
        super().__init__()

    def query_inventory(self, sku: str) -> list:
        result = self.call_api("/tools/inventory/query", "query_inventory", {"sku": sku})
        if not result.get("success"):
            raise Exception(result.get("message", "查询失败"))
        return result.get("data", [])

    def query_warehouse_stock(self, warehouse: str) -> list:
        result = self.call_api("/tools/inventory/query", "query_warehouse_stock", {"warehouse": warehouse})
        if not result.get("success"):
            raise Exception(result.get("message", "查询失败"))
        return result.get("data", [])
