from __future__ import annotations

from dataclasses import dataclass, field
from typing import cast
from uuid import UUID

from core.errors import SruliSigije
from core.handlers import ServiceRequest
from core.system.system import System
from core.transactions.handler_configurator import TransactionHandlerConfigurator
from core.transactions.repository import Transaction, TransactionRepository
from core.users.repository import UserRepository
from core.wallets.repository import WalletRepository


@dataclass
class TransactionService:
    users: UserRepository
    wallets: WalletRepository
    transactions: TransactionRepository
    system: System

    handler_configurator: TransactionHandlerConfigurator = field(init=False)

    def __post_init__(self) -> None:
        self.handler_configurator = TransactionHandlerConfigurator(
            users=self.users,
            wallets=self.wallets,
            transactions=self.transactions,
            system=self.system,
        )

    def create_transaction(
        self,
        sender_wallet_id: UUID,
        recipient_wallet_id: UUID,
        amount_btc: float,
        api_key: UUID,
    ) -> Transaction:
        request = ServiceRequest(logs=[])
        request.set_attribute("sender_wallet_id", sender_wallet_id)
        request.set_attribute("recipient_wallet_id", recipient_wallet_id)
        request.set_attribute("amount_btc", amount_btc)
        request.set_attribute("api_key", api_key)

        handler = self.handler_configurator.get_transaction_chain()
        handler.handle(request)

        if len(request.logs) > 0:
            for log in request.logs:
                print(log)
            raise SruliSigije

        return cast(Transaction, request.get_attribute("transaction"))
        # return request.get_attribute("transaction")

    def fetch_user_transactions(self, api_key: UUID) -> list[Transaction]:
        request = ServiceRequest(logs=[])
        request.set_attribute("api_key", api_key)
        handler = self.handler_configurator.get_user_transactions_chain()

        handler.handle(request)
        if len(request.logs) > 0:
            for log in request.logs:
                print(log)
            raise SruliSigije

        return cast(list[Transaction], request.get_attribute("performed_transactions"))

    def fetch_wallet_transactions(
        self, api_key: UUID, wallet_address: UUID
    ) -> list[Transaction]:
        request = ServiceRequest(logs=[])
        request.set_attribute("api_key", api_key)
        request.set_attribute("wallet_ids", [wallet_address])

        handler = self.handler_configurator.get_user_transactions_chain()
        handler.handle(request)

        if len(request.logs) > 0:
            for log in request.logs:
                print(log)
            raise SruliSigije

        return cast(list[Transaction], request.get_attribute("performed_transactions"))
