from decimal import Decimal
from typing import Optional
from sqlalchemy import text
from ..connection import get_session


class OrderDAO:

    def query_by_user(self, user_id: str) -> list[dict]:
        with get_session() as session:
            result = session.execute(
                text("SELECT id, order_no, user_id, status, total_amount, "
                     "DATE_FORMAT(created_at, '%Y-%m-%d %H:%i:%s') as created_at "
                     "FROM orders WHERE user_id = :uid"),
                {"uid": user_id}
            )
            return [dict(row._mapping) for row in result]

    def query_by_user_and_status(self, user_id: str, status: str) -> list[dict]:
        with get_session() as session:
            result = session.execute(
                text("SELECT id, order_no, user_id, status, total_amount, "
                     "DATE_FORMAT(created_at, '%Y-%m-%d %H:%i:%s') as created_at "
                     "FROM orders WHERE user_id = :uid AND status = :status"),
                {"uid": user_id, "status": status}
            )
            return [dict(row._mapping) for row in result]

    def query_by_order_no(self, order_no: str) -> Optional[dict]:
        with get_session() as session:
            result = session.execute(
                text("SELECT id, order_no, user_id, status, total_amount, "
                     "DATE_FORMAT(created_at, '%Y-%m-%d %H:%i:%s') as created_at "
                     "FROM orders WHERE order_no = :ono"),
                {"ono": order_no}
            )
            row = result.fetchone()
            return dict(row._mapping) if row else None

    def query_by_amount_range(self, user_id: str, min_amount: float, max_amount: float) -> list[dict]:
        with get_session() as session:
            result = session.execute(
                text("SELECT id, order_no, user_id, status, total_amount, "
                     "DATE_FORMAT(created_at, '%Y-%m-%d %H:%i:%s') as created_at "
                     "FROM orders WHERE user_id = :uid "
                     "AND total_amount >= :min_a AND total_amount <= :max_a"),
                {"uid": user_id, "min_a": min_amount, "max_a": max_amount}
            )
            return [dict(row._mapping) for row in result]

    def query_by_date_range(self, user_id: str, start_date: str, end_date: str) -> list[dict]:
        with get_session() as session:
            result = session.execute(
                text("SELECT id, order_no, user_id, status, total_amount, "
                     "DATE_FORMAT(created_at, '%Y-%m-%d %H:%i:%s') as created_at "
                     "FROM orders WHERE user_id = :uid "
                     "AND created_at >= :start_d AND created_at <= :end_d"),
                {"uid": user_id, "start_d": start_date, "end_d": end_date}
            )
            return [dict(row._mapping) for row in result]

    def query_by_conditions(
        self, user_id: str, status: str = None,
        min_amount: float = None, max_amount: float = None,
        start_date: str = None, end_date: str = None
    ) -> list[dict]:
        sql = ("SELECT id, order_no, user_id, status, total_amount, "
               "DATE_FORMAT(created_at, '%Y-%m-%d %H:%i:%s') as created_at "
               "FROM orders WHERE user_id = :uid")
        params = {"uid": user_id}

        if status:
            sql += " AND status = :status"
            params["status"] = status
        if min_amount is not None:
            sql += " AND total_amount >= :min_a"
            params["min_a"] = min_amount
        if max_amount is not None:
            sql += " AND total_amount <= :max_a"
            params["max_a"] = max_amount
        if start_date:
            sql += " AND created_at >= :start_d"
            params["start_d"] = start_date
        if end_date:
            sql += " AND created_at <= :end_d"
            params["end_d"] = end_date

        with get_session() as session:
            result = session.execute(text(sql), params)
            return [dict(row._mapping) for row in result]

    def count_by_user(self, user_id: str) -> int:
        with get_session() as session:
            result = session.execute(
                text("SELECT COUNT(*) as cnt FROM orders WHERE user_id = :uid"),
                {"uid": user_id}
            )
            return result.fetchone()._mapping["cnt"]

    def sum_amount_by_user(self, user_id: str) -> float:
        with get_session() as session:
            result = session.execute(
                text("SELECT COALESCE(SUM(total_amount), 0) as total FROM orders WHERE user_id = :uid"),
                {"uid": user_id}
            )
            return float(result.fetchone()._mapping["total"])

    def avg_amount_by_user(self, user_id: str) -> float:
        with get_session() as session:
            result = session.execute(
                text("SELECT COALESCE(AVG(total_amount), 0) as avg_a FROM orders WHERE user_id = :uid"),
                {"uid": user_id}
            )
            return float(result.fetchone()._mapping["avg_a"])

    def count_by_amount_range(self, user_id: str, min_amount: float, max_amount: float) -> int:
        with get_session() as session:
            result = session.execute(
                text("SELECT COUNT(*) as cnt FROM orders WHERE user_id = :uid "
                     "AND total_amount >= :min_a AND total_amount <= :max_a"),
                {"uid": user_id, "min_a": min_amount, "max_a": max_amount}
            )
            return result.fetchone()._mapping["cnt"]

    def sum_amount_by_amount_range(self, user_id: str, min_amount: float, max_amount: float) -> float:
        with get_session() as session:
            result = session.execute(
                text("SELECT COALESCE(SUM(total_amount), 0) as total FROM orders WHERE user_id = :uid "
                     "AND total_amount >= :min_a AND total_amount <= :max_a"),
                {"uid": user_id, "min_a": min_amount, "max_a": max_amount}
            )
            return float(result.fetchone()._mapping["total"])
