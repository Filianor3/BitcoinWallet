from typing import Annotated, Any, Union

from fastapi import Depends
from fastapi.requests import Request

from core.system.service import SystemService
from core.transactions.service import TransactionService
from core.users.service import UserService
from core.wallets.service import WalletService


def get_user_service(request: Request) -> Union[UserService, Any]:
    return request.app.state.user_service


UserServiceDependable = Annotated[UserService, Depends(get_user_service)]


def get_wallet_service(request: Request) -> Union[WalletService, Any]:
    return request.app.state.wallet_service


WalletServiceDependable = Annotated[WalletService, Depends(get_wallet_service)]


def get_transaction_service(request: Request) -> Union[TransactionService, Any]:
    return request.app.state.transaction_service


TransactionServiceDependable = Annotated[
    TransactionService, Depends(get_transaction_service)
]


def get_system_service(request: Request) -> Union[SystemService, Any]:
    return request.app.state.system_service


SystemServiceDependable = Annotated[SystemService, Depends(get_system_service)]
