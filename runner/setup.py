from fastapi import FastAPI

from core.system.service import SystemService
from core.transactions.service import TransactionService
from core.users.service import UserService
from core.wallets.service import WalletService
from infra.api.statistics import statistics_api
from infra.api.transactions import transaction_api
from infra.api.users import user_api
from infra.api.wallets import wallet_api
from infra.repositories.inmemory.system_inmemory import SystemInMemory
from infra.repositories.inmemory.transactions_inmemory import TransactionInMemory
from infra.repositories.inmemory.users_inmemory import UserInMemory
from infra.repositories.inmemory.wallets_inmemory import WalletInMemory
from infra.repositories.sqlite.db_manager import DbManager


def configure_app(
    app: FastAPI,
    user_service: UserService,
    wallet_service: WalletService,
    transaction_service: TransactionService,
    system_service: SystemService,
) -> None:
    app.include_router(user_api)
    app.include_router(wallet_api)
    app.include_router(transaction_api)
    app.include_router(statistics_api)
    app.state.user_service = user_service
    app.state.wallet_service = wallet_service
    app.state.transaction_service = transaction_service
    app.state.system_service = system_service


def init_test_app() -> FastAPI:
    app = FastAPI()
    users = UserInMemory()
    wallets = WalletInMemory()
    transactions = TransactionInMemory()
    system = SystemInMemory()
    configure_app(
        app,
        UserService(users=users),
        WalletService(users=users, wallets=wallets),
        TransactionService(
            users=users, wallets=wallets, transactions=transactions, system=system
        ),
        SystemService(users=users, system=system, transactions=transactions),
    )
    return app


def init_app() -> FastAPI:
    app = FastAPI()
    db_manager = DbManager()
    db_manager.drop_tables()
    db_manager.create_tables()
    users = db_manager.get_user_repository()
    wallets = db_manager.get_wallet_repository()
    transactions = db_manager.get_transaction_repository()
    system = db_manager.get_system()
    configure_app(
        app,
        UserService(users=users),
        WalletService(users=users, wallets=wallets),
        TransactionService(
            users=users, wallets=wallets, transactions=transactions, system=system
        ),
        SystemService(users=users, system=system, transactions=transactions),
    )
    return app
