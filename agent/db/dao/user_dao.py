from typing import Optional
from sqlalchemy import text
from ..connection import get_session


class UserDAO:

    def query_by_user_id(self, user_id: str) -> Optional[dict]:
        with get_session() as session:
            result = session.execute(
                text("SELECT id, user_id, name, phone, level, balance, "
                     "DATE_FORMAT(created_at, '%Y-%m-%d %H:%i:%s') as created_at "
                     "FROM users WHERE user_id = :uid"),
                {"uid": user_id}
            )
            row = result.fetchone()
            return dict(row._mapping) if row else None
