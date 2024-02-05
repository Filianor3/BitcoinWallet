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
#                                      TRANSACTION SERVICE SPECIFIC HANDLERS
# ======================================================================================================================


@dataclass
class FeeHandler(BaseHandler):
    wallets: WalletRepository
    successor: ServiceHandler = field(default_factory=EmptyHandler)

    def handle(self, request: ServiceRequest) -> None:
        sender_wallet_id = request.get_attribute("sender_wallet_id")
        recipient_wallet_id = request.get_attribute("recipient_wallet_id")
        api_key = request.get_attribute("api_key")

        if any(
            attr is None for attr in [sender_wallet_id, recipient_wallet_id, api_key]
        ):
            request.logs.append("Fee calculation skipped, missing required attributes")
        else:
            user_wallets = self.wallets.read_user_wallets(api_key)

            if sender_wallet_id not in [
                wallet.wallet_address for wallet in user_wallets
            ]:
                raise WalletOwnershipError("Sender wallet does not belong to the user")

            if recipient_wallet_id not in [
                wallet.wallet_address for wallet in user_wallets
            ]:
                request.set_attribute("fee", 0.015)
            else:
                request.set_attribute("fee", 0)

        self.successor.handle(request)


@dataclass
class WalletExistenceHandler(BaseHandler):
    wallets: WalletRepository
    successor: ServiceHandler = field(default_factory=EmptyHandler)

    def handle(self, request: ServiceRequest) -> None:
        sender_wallet_id = request.get_attribute("sender_wallet_id")
        recipient_wallet_id = request.get_attribute("recipient_wallet_id")

        if sender_wallet_id is None or recipient_wallet_id is None:
            request.logs.append(
                "Wallet existence check skipped, wallet_ids not provided"
            )
        else:
            try:
                sender_wallet = self.wallets.read(sender_wallet_id)
            except WalletDoesNotExistError as e:
                request.logs.append("Sender wallet does not exist")
                raise WalletDoesNotExistError("Sender wallet does not exist") from e

            try:
                recipient_wallet = self.wallets.read(recipient_wallet_id)
            except WalletDoesNotExistError as e:
                request.logs.append("Recipient wallet does not exist")
                raise WalletDoesNotExistError("Recipient wallet does not exist") from e

            request.set_attribute("sender_wallet", sender_wallet)
            request.set_attribute("recipient_wallet", recipient_wallet)

        self.successor.handle(request)


@dataclass
class BalanceCheckHandler(BaseHandler):
    successor: ServiceHandler = field(default_factory=EmptyHandler)

    def handle(self, request: ServiceRequest) -> None:
        sender_wallet = request.get_attribute("sender_wallet")
        amount_btc = request.get_attribute("amount_btc")
        fee = request.get_attribute("fee")
        if fee is None:
            fee = 0

        if sender_wallet is None or amount_btc is None:
            request.logs.append("Balance check skipped, missing required attributes")
        else:
            if amount_btc < 0:
                raise BadRequestError("Negative transaction amount")
            if sender_wallet.btc_balance < amount_btc * (1 + fee):
                raise InsufficientBalanceError(
                    "Insufficient balance in the sender's wallet"
                )

        self.successor.handle(request)


@dataclass
class TransactionExecutionHandler(BaseHandler):
    wallets: WalletRepository
    transactions: TransactionRepository
    system: System
    successor: ServiceHandler = field(default_factory=EmptyHandler)

    def handle(self, request: ServiceRequest) -> None:
        sender_wallet = request.get_attribute("sender_wallet")
        recipient_wallet = request.get_attribute("recipient_wallet")
        amount_btc = request.get_attribute("amount_btc")
        fee = request.get_attribute("fee")

        if (
            sender_wallet is None
            or recipient_wallet is None
            or amount_btc is None
            or fee is None
        ):
            request.logs.append(
                "Transaction execution skipped, missing required attributes"
            )
            self.successor.handle(request)
            return

        if len(request.logs) > 0:
            request.logs.append(
                "Transaction execution aborted, errors in previous steps"
            )
            self.successor.handle(request)
            return

        sender_wallet.btc_balance -= amount_btc * (1 + fee)
        recipient_wallet.btc_balance += amount_btc

        self.wallets.update(sender_wallet)
        self.wallets.update(recipient_wallet)

        transaction = Transaction(
            transaction_id=uuid4(),
            sender_wallet_id=sender_wallet.wallet_address,
            recipient_wallet_id=recipient_wallet.wallet_address,
            amount_btc=amount_btc,
            fee=fee,
            timestamp=datetime.utcnow(),
        )

        if fee > 0:
            profit = fee * amount_btc
            self.system.add_profitable_transaction(transaction.transaction_id, profit)

        self.transactions.create(transaction)
        request.set_attribute("transaction", transaction)

        self.successor.handle(request)


@dataclass
class WalletAddressesHandler(BaseHandler):
    wallets: WalletRepository
    successor: ServiceHandler = field(default_factory=EmptyHandler)

    def handle(self, request: ServiceRequest) -> None:
        api_key = request.get_attribute("api_key")

        if api_key is None:
            request.logs.append(
                "Wallet addresses retrieval skipped, no api_key provided"
            )
        else:
            user_wallets = self.wallets.read_user_wallets(api_key)
            wallet_addresses = [wallet.wallet_address for wallet in user_wallets]
            request.set_attribute("wallet_ids", wallet_addresses)

        self.successor.handle(request)


@dataclass
class FetchWithdrawalsHandler(BaseHandler):
    transactions: TransactionRepository
    successor: ServiceHandler = field(default_factory=EmptyHandler)

    def handle(self, request: ServiceRequest) -> None:
        wallet_ids = request.get_attribute("wallet_ids")
        if wallet_ids is None:
            request.logs.append(
                "Fetching withdrawals skipped, missing required wallet_ids"
            )
        else:
            transactions = request.get_attribute("performed_transactions") or []

            for wallet_id in wallet_ids:
                transactions += self.transactions.read_wallet_withdrawals(wallet_id)

            request.set_attribute("performed_transactions", transactions)

        self.successor.handle(request)


@dataclass
class FetchDepositsHandler(BaseHandler):
    transactions: TransactionRepository
    successor: ServiceHandler = field(default_factory=EmptyHandler)

    def handle(self, request: ServiceRequest) -> None:
        wallet_ids = request.get_attribute("wallet_ids")
        if wallet_ids is None:
            request.logs.append(
                "Fetching deposits skipped, missing required wallet_ids"
            )
        else:
            transactions = request.get_attribute("performed_transactions") or []

            for wallet_id in wallet_ids:
                transactions += self.transactions.read_wallet_deposits(wallet_id)
            request.set_attribute("performed_transactions", transactions)

        self.successor.handle(request)


# ======================================================================================================================
#                                        SYSTEM SERVICE SPECIFIC HANDLERS
# ======================================================================================================================


@dataclass
class IsAdminHandler(BaseHandler):
    system: System
    successor: ServiceHandler = field(default_factory=EmptyHandler)

    def handle(self, request: ServiceRequest) -> None:
        api_key = request.get_attribute("api_key")

        if api_key is not None:
            # print("Checking admin key...")
            if not self.system.get_admin_key() == api_key:
                raise ForbiddenError("Only admin can access statistics.")
        else:
            request.logs.append("admin key validation skipped, no api_key provided")

        self.successor.handle(request)


@dataclass
class GetStatisticsHandler(BaseHandler):
    system: System
    transactions: TransactionRepository
    successor: ServiceHandler = field(default_factory=EmptyHandler)

    def handle(self, request: ServiceRequest) -> None:
        total_transactions = len(self.transactions.read_all())
        platform_profit = self.system.get_platform_profit()

        request.set_attribute("total_transactions", total_transactions)
        request.set_attribute("platform_profit", platform_profit)

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
