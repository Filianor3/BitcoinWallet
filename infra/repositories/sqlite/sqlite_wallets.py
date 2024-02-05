import sqlite3
from dataclasses import dataclass
from uuid import UUID

from core.errors import WalletDoesNotExistError, WalletExistsError
from core.wallets.repository import Wallet, WalletRepository


@dataclass
class SQLiteWallets(WalletRepository):
    db_name: str

    def create(self, wallet: Wallet) -> None:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT 1 FROM wallets WHERE id = ?", (str(wallet.wallet_address),)
            )
            existing_wallet = cursor.fetchone()

            if existing_wallet:
                raise WalletExistsError(
                    f"Wallet with address '{wallet.wallet_address}' already exists"
                )

            cursor.execute(
                "INSERT INTO wallets (id, balance_btc) VALUES (?, ?)",
                (str(wallet.wallet_address), wallet.btc_balance),
            )

            cursor.execute(
                "INSERT INTO user_wallets (wallet_id, user_id) VALUES (?, ?)",
                (str(wallet.wallet_address), str(wallet.user_id)),
            )

    def read(self, wallet_id: UUID) -> Wallet:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT wallets.id, balance_btc, user_wallets.user_id
                FROM wallets
                JOIN user_wallets ON wallets.id = user_wallets.wallet_id
                WHERE wallets.id = ?
                """,
                (str(wallet_id),),
            )
            result = cursor.fetchone()

            if result:
                return Wallet(
                    wallet_address=UUID(result[0]),
                    btc_balance=result[1],
                    user_id=UUID(result[2]),
                )
            else:
                raise WalletDoesNotExistError(
                    f"Wallet with id '{wallet_id}' does not exist"
                )

    def update(self, wallet: Wallet) -> None:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT 1 FROM wallets WHERE id = ?", (str(wallet.wallet_address),)
            )
            existing_wallet = cursor.fetchone()

            if existing_wallet:
                cursor.execute(
                    "UPDATE wallets SET balance_btc = ? WHERE id = ?",
                    (wallet.btc_balance, str(wallet.wallet_address)),
                )

                cursor.execute(
                    "UPDATE user_wallets SET user_id = ? WHERE wallet_id = ?",
                    (str(wallet.user_id), str(wallet.wallet_address)),
                )
            else:
                raise WalletDoesNotExistError(
                    f"Wallet with address '{wallet.wallet_address}' does not exist"
                )

    def delete(self, wallet_id: UUID) -> None:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT 1 FROM wallets WHERE id = ?", (str(wallet_id),))
            existing_wallet = cursor.fetchone()

            if existing_wallet:
                cursor.execute("DELETE FROM wallets WHERE id = ?", (str(wallet_id),))

                cursor.execute(
                    "DELETE FROM user_wallets WHERE wallet_id = ?", (str(wallet_id),)
                )
            else:
                raise WalletDoesNotExistError(
                    f"Wallet with id '{wallet_id}' does not exist"
                )

    def read_all(self) -> list[Wallet]:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT wallets.id, balance_btc, user_wallets.user_id
                FROM wallets
                JOIN user_wallets ON wallets.id = user_wallets.wallet_id
                """
            )
            results = cursor.fetchall()

            return [
                Wallet(
                    wallet_address=UUID(result[0]),
                    btc_balance=result[1],
                    user_id=UUID(result[2]),
                )
                for result in results
            ]

    def read_user_wallets(self, user_id: UUID) -> list[Wallet]:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT wallet_id FROM user_wallets WHERE user_id = ?", (str(user_id),)
            )
            wallet_ids = cursor.fetchall()

            user_wallets = []

            for wallet_id in wallet_ids:
                cursor.execute(
                    "SELECT id, balance_btc FROM wallets WHERE id = ?", (wallet_id[0],)
                )
                result = cursor.fetchone()

                if result:
                    user_wallets.append(
                        Wallet(
                            user_id=user_id,
                            btc_balance=result[1],
                            wallet_address=UUID(result[0]),
                        )
                    )
                else:
                    raise WalletDoesNotExistError(
                        f"Wallet with id '{wallet_id[0]}' does not exist"
                    )

            return user_wallets
