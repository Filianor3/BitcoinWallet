from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core.errors import (
    BadRequestError,
    InsufficientBalanceError,
    UserDoesNotExistError,
    WalletDoesNotExistError,
    WalletOwnershipError,
)
from core.transactions.repository import Transaction
from infra.api.dependables import TransactionServiceDependable
from infra.api.error_responses import (
    create_bad_request_response,
    create_conflict_response,
    create_forbidden_response,
    create_not_found_response,
)

transaction_api = APIRouter(tags=["Transactions"])


def convert_transaction_for_response(transaction: Transaction) -> TransactionItem:
    return TransactionItem(
        transaction_id=transaction.transaction_id,
        sender_wallet_id=transaction.sender_wallet_id,
        recipient_wallet_id=transaction.recipient_wallet_id,
        amount_btc=transaction.amount_btc,
        fee=transaction.fee,
        timestamp=transaction.timestamp,
    )


class CreateTransactionRequest(BaseModel):
    sender_wallet_id: UUID
    recipient_wallet_id: UUID
    amount_btc: float


class TransactionItem(BaseModel):
    transaction_id: UUID
    sender_wallet_id: UUID
    recipient_wallet_id: UUID
    amount_btc: float
    fee: float
    timestamp: datetime


class TransactionItemEnvelope(BaseModel):
    transaction: TransactionItem


@transaction_api.post("/transactions", response_model=TransactionItemEnvelope)
async def create_transaction(
    request: CreateTransactionRequest,
    transaction_service: TransactionServiceDependable,
    api_key: UUID = Header(..., alias="X_API-KEY"),
) -> TransactionItemEnvelope | JSONResponse:
    try:
        transaction = transaction_service.create_transaction(
            sender_wallet_id=request.sender_wallet_id,
            recipient_wallet_id=request.recipient_wallet_id,
            amount_btc=request.amount_btc,
            api_key=api_key,
        )

        trans_item = convert_transaction_for_response(transaction)

        return TransactionItemEnvelope(transaction=trans_item)

    except UserDoesNotExistError as e:
        return create_not_found_response(message=str(e))

    except WalletDoesNotExistError as e:
        return create_not_found_response(message=str(e))

    except WalletOwnershipError as e:
        return create_forbidden_response(message=str(e))

    except InsufficientBalanceError as e:
        return create_conflict_response(message=str(e))

    except BadRequestError as e:
        return create_bad_request_response(message=str(e))


@transaction_api.get("/transactions", response_model=list[TransactionItem])
def get_user_transactions(
    transaction_service: TransactionServiceDependable,
    api_key: UUID = Header(..., alias="X_API-KEY"),
) -> list[TransactionItem] | JSONResponse:
    try:
        transactions = transaction_service.fetch_user_transactions(api_key)
        response = [
            TransactionItem(
                transaction_id=transaction.transaction_id,
                sender_wallet_id=transaction.sender_wallet_id,
                recipient_wallet_id=transaction.recipient_wallet_id,
                amount_btc=transaction.amount_btc,
                fee=transaction.fee,
                timestamp=transaction.timestamp,
            )
            for transaction in transactions
        ]

        return response

    except UserDoesNotExistError as e:
        return create_not_found_response(message=str(e))
