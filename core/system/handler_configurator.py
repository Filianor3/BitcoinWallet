from dataclasses import dataclass

from core.handlers import (
    GetStatisticsHandler,
    HandlerConfigurator,
    IsAdminHandler,
    ServiceHandler,
)
from core.system.system import System
from core.transactions.repository import TransactionRepository


@dataclass
class SystemHandlerConfigurator(HandlerConfigurator):
    system: System
    transactions: TransactionRepository

    def get_get_statistics_chain(self) -> ServiceHandler:
        return self._chain_handlers(
            [
                self.create_is_admin_handler(),
                self.create_get_statistics_handler(),
            ]
        )

    def create_is_admin_handler(self) -> ServiceHandler:
        return IsAdminHandler(system=self.system)

    def create_get_statistics_handler(self) -> ServiceHandler:
        return GetStatisticsHandler(system=self.system, transactions=self.transactions)
