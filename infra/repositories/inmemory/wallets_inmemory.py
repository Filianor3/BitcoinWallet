from dataclasses import dataclass, field
from uuid import UUID

from core.errors import WalletDoesNotExistError, WalletExistsError
from core.wallets.repository import Wallet, WalletRepository


@dataclass
class WalletInMemory(WalletRepository):
    wallets: dict[UUID, Wallet] = field(default_factory=dict)

    def create(self, wallet: Wallet) -> None:
        if wallet.wallet_address in self.wallets:
            raise WalletExistsError(
                f"Wallet with address '{wallet.wallet_address}' already exists"
            )

        self.wallets[wallet.wallet_address] = wallet

    def read(self, wallet_id: UUID) -> Wallet:
        try:
            return self.wallets[wallet_id]
        except KeyError:
            raise WalletDoesNotExistError(
                f"Wallet with id '{wallet_id}' does not exist"
            )

    def update(self, wallet: Wallet) -> None:
        if wallet.wallet_address in self.wallets:
            self.wallets[wallet.wallet_address] = wallet
        else:
            raise WalletDoesNotExistError(
                f"Wallet with address '{wallet.wallet_address}' does not exist"
            )

    def delete(self, wallet_id: UUID) -> None:
        try:
            del self.wallets[wallet_id]
        except KeyError:
            raise WalletDoesNotExistError(
                f"Wallet with id '{wallet_id}' does not exist"
            )

    def read_all(self) -> list[Wallet]:
        return list(self.wallets.values())

    def read_user_wallets(self, user_id: UUID) -> list[Wallet]:
        return [wallet for wallet in self.wallets.values() if wallet.user_id == user_id]
