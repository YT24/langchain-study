from sqlalchemy import text
from ..connection import get_session


class InventoryDAO:

    def query_by_sku(self, sku: str) -> list[dict]:
        with get_session() as session:
            result = session.execute(
                text("SELECT id, sku, warehouse, quantity, "
                     "DATE_FORMAT(updated_at, '%Y-%m-%d %H:%i:%s') as updated_at "
                     "FROM inventory WHERE sku = :sku"),
                {"sku": sku}
            )
            return [dict(row._mapping) for row in result]

    def query_by_warehouse(self, warehouse: str) -> list[dict]:
        with get_session() as session:
            result = session.execute(
                text("SELECT id, sku, warehouse, quantity, "
                     "DATE_FORMAT(updated_at, '%Y-%m-%d %H:%i:%s') as updated_at "
                     "FROM inventory WHERE warehouse = :wh"),
                {"wh": warehouse}
            )
            return [dict(row._mapping) for row in result]
