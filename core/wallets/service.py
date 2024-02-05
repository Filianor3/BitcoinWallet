from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple
from uuid import UUID

from core.errors import SruliSigije
from core.handlers import ServiceRequest
from core.users.repository import UserRepository
from core.wallets.handler_configurator import WalletHandlerConfigurator
from core.wallets.repository import Wallet, WalletRepository


@dataclass
class WalletService:
    users: UserRepository
    wallets: WalletRepository

    handler_configurator: WalletHandlerConfigurator = field(init=False)

    def __post_init__(self) -> None:
        self.handler_configurator = WalletHandlerConfigurator(
            users=self.users, wallets=self.wallets
        )

    def add_wallet(self, api_key: UUID) -> Tuple[Wallet, float]:
        # Create a ServiceRequest
        request = ServiceRequest(logs=[])
        request.set_attribute("api_key", api_key)
        handler = self.handler_configurator.get_add_wallet_chain()

        handler.handle(request)
        if len(request.logs) > 0:
            # Log errors and return None
            for log in request.logs:
                print(log)
                raise SruliSigije

        return (
            request.get_attribute("wallet"),
            request.get_attribute("wallet").btc_balance
            * request.get_attribute("exchange_rate"),
        )

    def fetch_wallet(self, api_key: UUID, wallet_id: UUID) -> Tuple[Wallet, float]:
        request = ServiceRequest(logs=[])
        request.set_attribute("api_key", api_key)
        request.set_attribute("wallet_id", wallet_id)
        handler = self.handler_configurator.get_wallet_fetch_chain()

        handler.handle(request)

        if len(request.logs) > 0:
            # Log errors and return None
            for log in request.logs:
                print(log)
                raise SruliSigije

        return (
            request.get_attribute("wallet"),
            request.get_attribute("wallet").btc_balance
            * request.get_attribute("exchange_rate"),
        )
