from dataclasses import dataclass, field
from uuid import UUID

from core.errors import ForbiddenError
from core.handlers import ServiceRequest
from core.system.handler_configurator import SystemHandlerConfigurator
from core.system.system import System
from core.transactions.repository import TransactionRepository
from core.users.repository import UserRepository


@dataclass
class SystemService:
    users: UserRepository
    transactions: TransactionRepository
    system: System

    handler_configurator: SystemHandlerConfigurator = field(init=False)

    def __post_init__(self) -> None:
        self.handler_configurator = SystemHandlerConfigurator(
            users=self.users, transactions=self.transactions, system=self.system
        )

    def get_statistics(self, api_key: UUID) -> dict[str, float]:
        request = ServiceRequest(logs=[])
        request.set_attribute("api_key", api_key)

        handler = self.handler_configurator.get_get_statistics_chain()

        handler.handle(request)
        if len(request.logs) > 0:
            for log in request.logs:
                print(log)
            raise ForbiddenError("Only admin can access statistics.")

        return {
            "total_transactions": request.get_attribute("total_transactions"),
            "platform_profit": request.get_attribute("platform_profit"),
        }

    def is_admin(self, api_key: UUID) -> bool:
        admin_key = self.system.get_admin_key()
        return api_key == admin_key
