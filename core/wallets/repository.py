from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass
class Wallet:
    user_id: UUID
    btc_balance: float
    wallet_address: UUID


class WalletRepository(Protocol):
    def create(self, wallet: Wallet) -> None:
        # inmemory case: simply store wallet in the dict
        # sqlite case: store wallet fields in user_wallets and wallets tables
        pass

    def read(self, wallet_id: UUID) -> Wallet:
        pass

    def update(self, wallet: Wallet) -> None:
        pass

    def delete(self, wallet_id: UUID) -> None:
        pass

    def read_all(self) -> list[Wallet]:
        pass

    def read_user_wallets(self, user_id: UUID) -> list[Wallet]:
        pass
