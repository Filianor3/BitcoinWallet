from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List
from uuid import UUID

from core.errors import TransactionDoesNotExistError, TransactionExistsError
from core.transactions.repository import Transaction, TransactionRepository


@dataclass
class TransactionInMemory(TransactionRepository):
    transactions: Dict[UUID, Transaction] = field(default_factory=dict)

    def create(self, transaction: Transaction) -> None:
        if transaction.transaction_id in self.transactions:
            raise TransactionExistsError(
                f"Transaction with ID {transaction.transaction_id} already exists"
            )
        self.transactions[transaction.transaction_id] = transaction

    def read(self, transaction_id: UUID) -> Transaction:
        transaction = self.transactions.get(transaction_id)
        if transaction is None:
            raise TransactionDoesNotExistError(
                f"Transaction with ID {transaction_id} does not exist"
            )
        return transaction

    def update(self, transaction: Transaction) -> None:
        if transaction.transaction_id in self.transactions:
            self.transactions[transaction.transaction_id] = transaction
        else:
            raise TransactionDoesNotExistError(
                f"Transaction with ID {transaction.transaction_id} does not exist"
            )

    def delete(self, transaction_id: UUID) -> None:
        if transaction_id in self.transactions:
            del self.transactions[transaction_id]
        else:
            raise TransactionDoesNotExistError(
                f"Transaction with ID {transaction_id} does not exist"
            )

    def read_all(self) -> List[Transaction]:
        return list(self.transactions.values())

    def read_wallet_deposits(self, wallet_id: UUID) -> List[Transaction]:
        return [
            t for t in self.transactions.values() if t.recipient_wallet_id == wallet_id
        ]

    def read_wallet_withdrawals(self, wallet_id: UUID) -> List[Transaction]:
        return [
            t for t in self.transactions.values() if t.sender_wallet_id == wallet_id
        ]
