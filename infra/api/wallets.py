from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Header, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core.errors import (
    UserDoesNotExistError,
    WalletDoesNotExistError,
    WalletLimitError,
    WalletOwnershipError,
)
from core.wallets.repository import Wallet
from infra.api.dependables import TransactionServiceDependable, WalletServiceDependable
from infra.api.error_responses import (
    create_conflict_response,
    create_forbidden_response,
    create_not_found_response,
)
from infra.api.transactions import TransactionItem, convert_transaction_for_response

wallet_api = APIRouter(tags=["Wallets"])


def convert_wallet_for_response(wallet: Wallet, balance_usd: float) -> WalletItem:
    return WalletItem(
        wallet_address=wallet.wallet_address,
        balance_btc=wallet.btc_balance,
        balance_usd=balance_usd,
    )


class WalletItem(BaseModel):
    wallet_address: UUID
    balance_btc: float
    balance_usd: float


class WalletItemEnvelope(BaseModel):
    wallet: WalletItem


@wallet_api.post(
    "/wallets", status_code=status.HTTP_201_CREATED, response_model=WalletItemEnvelope
)
async def create_wallet(
    wallet_service: WalletServiceDependable,
    api_key: UUID = Header(..., alias="X_API-KEY"),
) -> WalletItemEnvelope | JSONResponse:
    try:
        wallet, usd_balance = wallet_service.add_wallet(api_key)
        wallet_item = convert_wallet_for_response(wallet, usd_balance)
        return WalletItemEnvelope(wallet=wallet_item)

    except UserDoesNotExistError as e:
        return create_not_found_response(message=str(e))
    except WalletLimitError as e:
        return create_conflict_response(message=str(e))


@wallet_api.get(
    "/wallets/{address}",
    status_code=status.HTTP_200_OK,
    response_model=WalletItemEnvelope,
)
def get_wallet(
    address: UUID,
    wallet_service: WalletServiceDependable,
    api_key: UUID = Header(..., alias="X_API-KEY"),
) -> WalletItemEnvelope | JSONResponse:
    try:
        wallet, usd_balance = wallet_service.fetch_wallet(
            api_key=api_key, wallet_id=address
        )

        wallet_item = convert_wallet_for_response(wallet, usd_balance)
        return WalletItemEnvelope(wallet=wallet_item)

    except UserDoesNotExistError as e:
        return create_not_found_response(message=str(e))

    except WalletOwnershipError as e:
        return create_forbidden_response(message=str(e))

    except WalletDoesNotExistError as e:
        return create_not_found_response(message=str(e))


@wallet_api.get(
    "/wallets/{address}/transactions",
    status_code=status.HTTP_200_OK,
    response_model=list[TransactionItem],
)
def get_wallet_transactions(
    address: UUID,
    transaction_service: TransactionServiceDependable,
    api_key: UUID = Header(..., alias="X_API-KEY"),
) -> list[TransactionItem] | JSONResponse:
    try:
        transactions = transaction_service.fetch_wallet_transactions(
            api_key=api_key, wallet_address=address
        )
        response = [
            convert_transaction_for_response(transaction)
            for transaction in transactions
        ]
        return response

    except UserDoesNotExistError as e:
        return create_not_found_response(message=str(e))
    except WalletOwnershipError as e:
        return create_forbidden_response(message=str(e))
    except WalletDoesNotExistError as e:
        return create_not_found_response(message=str(e))
