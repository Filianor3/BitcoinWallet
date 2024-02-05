import sqlite3
from dataclasses import dataclass

from infra.repositories.sqlite.sqlite_system import SQLiteSystem
from infra.repositories.sqlite.sqlite_trasactions import SQLiteTransactions
from infra.repositories.sqlite.sqlite_users import SQLiteUsers
from infra.repositories.sqlite.sqlite_wallets import SQLiteWallets


@dataclass
class DbManager:
    db_name: str = "btc_wallet.db"

    def create_tables(self) -> None:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE,
                    password TEXT
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS wallets (
                    id TEXT PRIMARY KEY,
                    balance_btc REAL
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS user_wallets (
                    wallet_id TEXT,
                    user_id TEXT,
                    PRIMARY KEY (wallet_id, user_id),
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (wallet_id) REFERENCES wallets (id)
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    id TEXT PRIMARY KEY,
                    sender_wallet_id TEXT,
                    recipient_wallet_id TEXT,
                    amount_btc REAL,
                    fee_pct REAL,
                    trans_timestamp TIMESTAMP,
                    FOREIGN KEY (sender_wallet_id) REFERENCES wallets (id),
                    FOREIGN KEY (recipient_wallet_id) REFERENCES wallets (id)
                )
                """
            )

            cursor.execute(
                """
                  CREATE TABLE IF NOT EXISTS system_data (
                    transaction_id TEXT PRIMARY KEY,
                    profit REAL,
                    FOREIGN KEY (transaction_id) REFERENCES transactions (id)
                );
                """
            )

    def drop_tables(self) -> None:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS users")
            cursor.execute("DROP TABLE IF EXISTS wallets")
            cursor.execute("DROP TABLE IF EXISTS user_wallets")
            cursor.execute("DROP TABLE IF EXISTS transactions")
            cursor.execute("DROP TABLE IF EXISTS system_data")

    def get_user_repository(self) -> SQLiteUsers:
        return SQLiteUsers(self.db_name)

    def get_wallet_repository(self) -> SQLiteWallets:
        return SQLiteWallets(self.db_name)

    def get_transaction_repository(self) -> SQLiteTransactions:
        return SQLiteTransactions(self.db_name)

    def get_system(self) -> SQLiteSystem:
        return SQLiteSystem(self.db_name)
