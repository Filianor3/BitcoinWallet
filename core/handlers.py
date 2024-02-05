from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, Protocol
from uuid import uuid4

from core.converter import Converter
from core.errors import (
    BadRequestError,
    ForbiddenError,
    InsufficientBalanceError,
    UserDoesNotExistError,
    WalletDoesNotExistError,
    WalletLimitError,
    WalletOwnershipError,
)
from core.system.system import System
from core.transactions.repository import Transaction, TransactionRepository
from core.users.repository import UserRepository
from core.wallets.repository import Wallet, WalletRepository
from infra.converter_coinconvert_api import CoinConvertConverter


@dataclass
class ServiceRequest:
    _data: dict[str, Any] = field(default_factory=dict)
    logs: list[str] = field(default_factory=list)

    def get_attribute(self, key: str, default: Optional[Any] = None) -> Any:
        return self._data.get(key, default)

    def set_attribute(self, key: str, value: Any) -> None:
        self._data[key] = value

    def to_dict(self) -> dict[str, Any]:
        return self._data


class ServiceHandler(Protocol):
    def handle(self, request: ServiceRequest) -> None:
        pass

    def set_next(self, next_handler: ServiceHandler) -> ServiceHandler:
        pass


@dataclass
class EmptyHandler:
    def handle(self, request: ServiceRequest) -> None:
        pass

    def set_next(self, next_handler: ServiceHandler) -> ServiceHandler:
        return next_handler


class BaseHandler(ServiceHandler):
    def __init__(self) -> None:
        self.successor: Optional[ServiceHandler] = None

    def handle(self, request: ServiceRequest) -> None:
        raise NotImplementedError("Subclasses must implement the 'handle' method")

    def set_next(self, next_handler: ServiceHandler) -> ServiceHandler:
        self.successor = next_handler
        return next_handler


# ======================================================================================================================
#                                              GENERAL USE HANDLERS
# ======================================================================================================================


@dataclass
class ApiKeyValidationHandler(BaseHandler):
    users: UserRepository
    successor: ServiceHandler = field(default_factory=EmptyHandler)

    def handle(self, request: ServiceRequest) -> None:
        api_key = request.get_attribute("api_key")
        if api_key is not None:
            try:
                # print("Checking existence...")
                self.users.read(api_key)
            except UserDoesNotExistError as e:
                raise e
        else:
            request.logs.append("API key validation skipped, no api_key provided")

        self.successor.handle(request)


@dataclass
class BtcConversionHandler(BaseHandler):
    converter: Converter = field(default_factory=CoinConvertConverter)
    successor: ServiceHandler = field(default_factory=EmptyHandler)

    def handle(self, request: ServiceRequest) -> None:
        amount = 1
        conversion_response = self.converter.get_conversion(
            from_symbol="btc", to_symbol="usd", amount=amount
        )

        request.set_attribute("exchange_rate", conversion_response["USD"])
        self.successor.handle(request)


# ======================================================================================================================
#                                        WALLET SERVICE SPECIFIC HANDLERS
# ======================================================================================================================


@dataclass
class WalletCountHandler(BaseHandler):
    wallets: WalletRepository
    successor: ServiceHandler = field(default_factory=EmptyHandler)

    def handle(self, request: ServiceRequest) -> None:
        api_key = request.get_attribute("api_key")

        if api_key is not None:
            # print("Counting wallets ")
            user_wallets = self.wallets.read_user_wallets(api_key)
            if len(user_wallets) >= 3:
                raise WalletLimitError(
                    "Maximum number of wallets reached for this user"
                )
        else:
            request.logs.append("Wallet count skipped, no api_key provided")

        self.successor.handle(request)


@dataclass
class WalletRegistrationHandler(BaseHandler):
    wallets: WalletRepository
    successor: ServiceHandler = field(default_factory=EmptyHandler)

    def handle(self, request: ServiceRequest) -> None:
        api_key = request.get_attribute("api_key")

        if api_key is not None:
            # print("Creating wallet ")
            created_wallet = Wallet(
                user_id=api_key,
                btc_balance=1.0,  # Initial deposit of 1 BTC
                wallet_address=uuid4(),
            )
            self.wallets.create(created_wallet)
            request.set_attribute("wallet_id", created_wallet.wallet_address)
            request.set_attribute("wallet", created_wallet)
        else:
            request.logs.append("Wallet Registration skipped, no api_key provided")

        self.successor.handle(request)


@dataclass
class WalletOwnershipHandler(BaseHandler):
    wallets: WalletRepository
    successor: ServiceHandler = field(default_factory=EmptyHandler)

    def handle(self, request: ServiceRequest) -> None:
        api_key = request.get_attribute("api_key")
        wallet_id = request.get_attribute("wallet_id")

        if api_key is None:
            request.logs.append("Wallet ownership check skipped, no api_key provided")
        elif wallet_id is None:
            request.logs.append("Wallet ownership check skipped, no wallet_id provided")
        else:
            # print("Checking wallet ownership ")
            user_wallets = self.wallets.read_user_wallets(api_key)
            if wallet_id not in [wallet.wallet_address for wallet in user_wallets]:
                raise WalletOwnershipError(
                    f"Wallet with ID '{wallet_id}' does not belong to the user"
                )

        self.successor.handle(request)


@dataclass
class WalletFetchHandler(BaseHandler):
    wallets: WalletRepository
    successor: ServiceHandler = field(default_factory=EmptyHandler)

    def handle(self, request: ServiceRequest) -> None:
        wallet_id = request.get_attribute("wallet_id")

        if wallet_id is not None:
            # print("Reading wallet ")
            try:
                wallet = self.wallets.read(wallet_id)
                request.set_attribute("wallet", wallet)
            except WalletDoesNotExistError as e:
                raise e

        else:
            request.logs.append("Wallet fetch skipped, wallet_id was not provided")

        self.successor.handle(request)




# ======================================================================================================================
#                                      HANDLER CONFIGURATOR BASE CLASS
# ======================================================================================================================


@dataclass
class HandlerConfigurator:
    users: UserRepository

    def _chain_handlers(self, handlers: list[ServiceHandler]) -> ServiceHandler:
        # Helper function to chain a list of handlers
        if not handlers:
            return EmptyHandler()
        for i in range(len(handlers) - 1):
            handlers[i].set_next(handlers[i + 1])
        return handlers[0]

    def create_api_key_validation_handler(self) -> ServiceHandler:
        return ApiKeyValidationHandler(users=self.users)

    def create_conversion_handler(self) -> ServiceHandler:
        return BtcConversionHandler()
