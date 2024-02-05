from dataclasses import dataclass

from core.handlers import (
    HandlerConfigurator,
    ServiceHandler,
    WalletCountHandler,
    WalletFetchHandler,
    WalletOwnershipHandler,
    WalletRegistrationHandler,
)
from core.wallets.repository import WalletRepository


@dataclass
class WalletHandlerConfigurator(HandlerConfigurator):
    # users: UserRepository
    wallets: WalletRepository

    def get_add_wallet_chain(self) -> ServiceHandler:
        return self._chain_handlers(
            [
                self.create_api_key_validation_handler(),
                self.create_count_handler(),
                self.create_registration_handler(),
                self.create_fetch_handler(),
                self.create_conversion_handler(),
            ]
        )

    def get_wallet_fetch_chain(self) -> ServiceHandler:
        return self._chain_handlers(
            [
                self.create_api_key_validation_handler(),
                self.create_fetch_handler(),
                self.create_ownership_handler(),
                self.create_conversion_handler(),
            ]
        )

    def create_count_handler(self) -> ServiceHandler:
        return WalletCountHandler(wallets=self.wallets)

    def create_registration_handler(self) -> ServiceHandler:
        return WalletRegistrationHandler(wallets=self.wallets)

    def create_fetch_handler(self) -> ServiceHandler:
        return WalletFetchHandler(wallets=self.wallets)

    def create_ownership_handler(self) -> ServiceHandler:
        return WalletOwnershipHandler(wallets=self.wallets)
