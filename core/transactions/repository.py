from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID


@dataclass
class Transaction:
    transaction_id: UUID
    sender_wallet_id: UUID
    recipient_wallet_id: UUID
    amount_btc: float
    fee: float
    timestamp: datetime


class TransactionRepository(Protocol):
    def create(self, transaction: Transaction) -> None:
        """Create a new transaction."""
        pass

    def read(self, transaction_id: UUID) -> Transaction:
        """Read a transaction by its ID."""
        pass

    def update(self, transaction: Transaction) -> None:
        """Update an existing transaction."""
        pass

    def delete(self, transaction_id: UUID) -> None:
        """Delete a transaction by its ID."""
        pass

    def read_all(self) -> list[Transaction]:
        """Read all transactions."""
        pass

    def read_wallet_deposits(self, wallet_id: UUID) -> list[Transaction]:
        """Read all deposit transactions associated with a wallet."""
        pass

    def read_wallet_withdrawals(self, wallet_id: UUID) -> list[Transaction]:
        """Read all withdrawal transactions associated with a wallet."""
        pass
