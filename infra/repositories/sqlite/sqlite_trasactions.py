from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import List
from uuid import UUID

from core.errors import TransactionDoesNotExistError, TransactionExistsError
from core.transactions.repository import Transaction, TransactionRepository


@dataclass
class SQLiteTransactions(TransactionRepository):
    db_name: str

    def create(self, transaction: Transaction) -> None:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT 1 FROM transactions WHERE id = ?",
                (str(transaction.transaction_id),),
            )
            existing_transaction = cursor.fetchone()
            if existing_transaction:
                raise TransactionExistsError(
                    f"Transaction with ID {transaction.transaction_id} already exists"
                )

            cursor.execute(
                """
                INSERT INTO transactions
                            (id, sender_wallet_id,
                            recipient_wallet_id,
                            amount_btc, fee_pct,
                            trans_timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(transaction.transaction_id),
                    str(transaction.sender_wallet_id),
                    str(transaction.recipient_wallet_id),
                    transaction.amount_btc,
                    transaction.fee,
                    transaction.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f"),
                ),
            )

    def read(self, transaction_id: UUID) -> Transaction:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT  id,
                        sender_wallet_id,
                        recipient_wallet_id,
                        amount_btc, fee_pct,
                        trans_timestamp
                  FROM  transactions
                 WHERE  id = ?
                """,
                (str(transaction_id),),
            )
            result = cursor.fetchone()

            if result:
                return Transaction(
                    transaction_id=UUID(result[0]),
                    sender_wallet_id=UUID(result[1]),
                    recipient_wallet_id=UUID(result[2]),
                    amount_btc=result[3],
                    fee=result[4],
                    timestamp=datetime.strptime(result[5], "%Y-%m-%d %H:%M:%S.%f"),
                )
            else:
                raise TransactionDoesNotExistError(
                    f"Transaction with ID {transaction_id} does not exist"
                )

    def update(self, transaction: Transaction) -> None:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT 1 FROM transactions WHERE id = ?",
                (str(transaction.transaction_id),),
            )
            existing_transaction = cursor.fetchone()
            if existing_transaction:
                cursor.execute(
                    """
                    UPDATE transactions
                    SET sender_wallet_id = ?,
                        recipient_wallet_id = ?,
                        amount_btc = ?, fee_pct = ?,
                        trans_timestamp = ?
                    WHERE id = ?
                    """,
                    (
                        str(transaction.sender_wallet_id),
                        str(transaction.recipient_wallet_id),
                        transaction.amount_btc,
                        transaction.fee,
                        transaction.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f"),
                        str(transaction.transaction_id),
                    ),
                )
            else:
                raise TransactionDoesNotExistError(
                    f"Transaction with ID {transaction.transaction_id} does not exist"
                )

    def delete(self, transaction_id: UUID) -> None:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT 1 FROM transactions WHERE id = ?", (str(transaction_id),)
            )
            existing_transaction = cursor.fetchone()
            if existing_transaction:
                cursor.execute(
                    "DELETE FROM transactions WHERE id = ?", (str(transaction_id),)
                )
            else:
                raise TransactionDoesNotExistError(
                    f"Transaction with ID {transaction_id} does not exist"
                )

    def read_all(self) -> List[Transaction]:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT  id,
                        sender_wallet_id,
                        recipient_wallet_id,
                        amount_btc, fee_pct,
                        trans_timestamp
                  FROM  transactions
                """
            )
            results = cursor.fetchall()

            return [
                Transaction(
                    transaction_id=UUID(result[0]),
                    sender_wallet_id=UUID(result[1]),
                    recipient_wallet_id=UUID(result[2]),
                    amount_btc=result[3],
                    fee=result[4],
                    timestamp=datetime.strptime(result[5], "%Y-%m-%d %H:%M:%S.%f"),
                )
                for result in results
            ]

    def read_wallet_deposits(self, wallet_id: UUID) -> List[Transaction]:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT  id,
                        sender_wallet_id,
                        recipient_wallet_id,
                        amount_btc, fee_pct,
                        trans_timestamp
                  FROM  transactions
                 WHERE  recipient_wallet_id = ?
                """,
                (str(wallet_id),),
            )
            results = cursor.fetchall()

            return [
                Transaction(
                    transaction_id=UUID(result[0]),
                    sender_wallet_id=UUID(result[1]),
                    recipient_wallet_id=UUID(result[2]),
                    amount_btc=result[3],
                    fee=result[4],
                    timestamp=datetime.strptime(result[5], "%Y-%m-%d %H:%M:%S.%f"),
                )
                for result in results
            ]

    def read_wallet_withdrawals(self, wallet_id: UUID) -> List[Transaction]:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT  id,
                        sender_wallet_id,
                        recipient_wallet_id,
                        amount_btc,
                        fee_pct,
                        trans_timestamp
                  FROM  transactions
                 WHERE  sender_wallet_id = ?
                """,
                (str(wallet_id),),
            )
            results = cursor.fetchall()

            return [
                Transaction(
                    transaction_id=UUID(result[0]),
                    sender_wallet_id=UUID(result[1]),
                    recipient_wallet_id=UUID(result[2]),
                    amount_btc=result[3],
                    fee=result[4],
                    timestamp=datetime.strptime(result[5], "%Y-%m-%d %H:%M:%S.%f"),
                )
                for result in results
            ]
