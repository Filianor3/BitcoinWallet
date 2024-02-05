from typing import Protocol
from uuid import UUID


class System(Protocol):
    def add_profitable_transaction(self, transaction_id: UUID, profit: float) -> None:
        pass

    def get_platform_profit(self) -> float:
        pass

    def get_admin_key(self) -> UUID:
        pass
