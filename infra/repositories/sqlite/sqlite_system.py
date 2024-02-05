from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from uuid import UUID

from core.system.system import System


@dataclass
class SQLiteSystem(System):
    db_name: str

    def add_profitable_transaction(self, transaction_id: UUID, profit: float) -> None:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO system_data (transaction_id, profit)
                VALUES (?, ?)
                """,
                (str(transaction_id), profit),
            )

    def get_platform_profit(self) -> float:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT SUM(profit) FROM system_data")
            result = cursor.fetchone()

            return float(result[0]) if result and result[0] else 0.0

    def get_admin_key(self) -> UUID:
        admin_key_str = os.getenv("ADMIN_KEY")

        default_admin_key = "086048b2-e07a-4e45-843b-0e5d2aa2483b"
        admin_key_str = admin_key_str or default_admin_key

        admin_key = UUID(admin_key_str)
        return admin_key
