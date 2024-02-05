from dataclasses import dataclass

from core.handlers import (
    BalanceCheckHandler,
    FeeHandler,
    FetchDepositsHandler,
    FetchWithdrawalsHandler,
    HandlerConfigurator,
    ServiceHandler,
    TransactionExecutionHandler,
    WalletAddressesHandler,
    WalletExistenceHandler,
)
from core.system.system import System
from core.transactions.repository import TransactionRepository
from core.wallets.repository import WalletRepository


@dataclass
class TransactionHandlerConfigurator(HandlerConfigurator):
    # users: UserRepository
    wallets: WalletRepository
    transactions: TransactionRepository
    system: System

    def get_transaction_chain(self) -> ServiceHandler:
        return self._chain_handlers(
            [
                self.create_api_key_validation_handler(),
                self.create_wallet_existence_handler(),
                self.create_fee_handler(),
                self.create_balance_check_handler(),
                self.create_transaction_execution_handler(),
            ]
        )

    def get_wallet_transactions_chain(self) -> ServiceHandler:
        return self._chain_handlers(
            [
                self.create_api_key_validation_handler(),
                self.create_fetch_deposits_handler(),
                self.create_fetch_withdrawals_handler(),
            ]
        )

    def get_user_transactions_chain(self) -> ServiceHandler:
        return self._chain_handlers(
            [
                self.create_api_key_validation_handler(),
                self.create_wallets_addresses_handler(),
                self.create_fetch_withdrawals_handler(),
            ]
        )

    # def create_api_key_validation_handler(self) -> ServiceHandler:
    #     return ApiKeyValidationHandler(users=self.users)

    def create_fee_handler(self) -> ServiceHandler:
        return FeeHandler(wallets=self.wallets)

    def create_wallet_existence_handler(self) -> ServiceHandler:
        return WalletExistenceHandler(wallets=self.wallets)

    def create_balance_check_handler(self) -> ServiceHandler:
        return BalanceCheckHandler()

    def create_transaction_execution_handler(self) -> ServiceHandler:
        return TransactionExecutionHandler(
            wallets=self.wallets, transactions=self.transactions, system=self.system
        )

    def create_wallets_addresses_handler(self) -> ServiceHandler:
        return WalletAddressesHandler(wallets=self.wallets)

    def create_fetch_withdrawals_handler(self) -> ServiceHandler:
        return FetchWithdrawalsHandler(transactions=self.transactions)

    def create_fetch_deposits_handler(self) -> ServiceHandler:
        return FetchDepositsHandler(transactions=self.transactions)
