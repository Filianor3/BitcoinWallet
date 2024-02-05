import os
from dataclasses import dataclass, field
from uuid import UUID

from dotenv import load_dotenv

from core.system.system import System

load_dotenv()


@dataclass
class SystemInMemory(System):
    transactions: dict[UUID, float] = field(default_factory=dict)

    def add_profitable_transaction(self, transaction_id: UUID, profit: float) -> None:
        self.transactions[transaction_id] = profit

    def get_platform_profit(self) -> float:
        total_profit = sum(self.transactions.values())
        return total_profit

    def get_admin_key(self) -> UUID:
        admin_key_str = os.getenv("ADMIN_KEY")

        # If the environment variable is not set, use a default value
        default_admin_key = "086048b2-e07a-4e45-843b-0e5d2aa2483b"
        admin_key_str = admin_key_str or default_admin_key

        admin_key = UUID(admin_key_str)
        return admin_key
