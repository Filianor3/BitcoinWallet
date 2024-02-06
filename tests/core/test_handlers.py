from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

import pytest

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
from core.handlers import (
    ApiKeyValidationHandler,
    BalanceCheckHandler,
    BaseHandler,
    BtcConversionHandler,
    EmptyHandler,
    FeeHandler,
    FetchDepositsHandler,
    FetchWithdrawalsHandler,
    GetStatisticsHandler,
    IsAdminHandler,
    ServiceHandler,
    ServiceRequest,
    TransactionExecutionHandler,
    WalletAddressesHandler,
    WalletCountHandler,
    WalletExistenceHandler,
    WalletFetchHandler,
    WalletOwnershipHandler,
    WalletRegistrationHandler,
)
from core.system.system import System
from core.transactions.repository import TransactionRepository
from core.users.repository import UserRepository
from core.wallets.repository import Wallet, WalletRepository
from infra.repositories.inmemory.system_inmemory import SystemInMemory
from infra.repositories.inmemory.transactions_inmemory import TransactionInMemory
from infra.repositories.inmemory.users_inmemory import UserInMemory
from infra.repositories.inmemory.wallets_inmemory import WalletInMemory
from tests.fake import FakeGenerator


@pytest.fixture
def users_repository() -> UserRepository:
    return UserInMemory()


@pytest.fixture
def wallets_repository() -> WalletRepository:
    return WalletInMemory()


@pytest.fixture
def transactions_repository() -> TransactionRepository:
    return TransactionInMemory()


class ConverterMock:
    def get_conversion(
        self, from_symbol: str, to_symbol: str, amount: float
    ) -> dict[str, Any]:
        return {"USD": 40000}


@pytest.fixture
def converter_mock() -> Converter:
    return ConverterMock()


@pytest.fixture
def system() -> System:
    return SystemInMemory()


# ======================================================================================================================
#                                              GENERAL USE HANDLER TESTS
# ======================================================================================================================


def test_set_next() -> None:
    class TestHandler(BaseHandler):
        def handle(self, request: ServiceRequest) -> None:
            pass

    handler1 = TestHandler()
    handler2 = TestHandler()
    handler3 = TestHandler()

    handler1.set_next(handler2).set_next(handler3)

    assert handler1.successor == handler2
    assert handler2.successor == handler3
    assert handler3.successor is None


def test_handle_with_next_handler() -> None:
    @dataclass
    class TestHandlerA(BaseHandler):
        successor: ServiceHandler = field(default_factory=EmptyHandler)

        def handle(self, request: ServiceRequest) -> None:
            request.set_attribute("a_handled", True)
            self.successor.handle(request)

    class TestHandlerB(BaseHandler):
        def handle(self, request: ServiceRequest) -> None:
            request.set_attribute("b_handled", True)

    handler1 = TestHandlerA()
    handler2 = TestHandlerB()

    handler1.set_next(handler2)

    request = ServiceRequest()
    handler1.handle(request)

    assert request.get_attribute("a_handled")
    assert request.get_attribute("b_handled")


def test_api_key_validation_handler_with_api_key(
    users_repository: UserRepository, wallets_repository: WalletRepository
) -> None:
    generator = FakeGenerator()
    user = generator.generate_user()
    users_repository.create(user)

    request = ServiceRequest()
    request.set_attribute("api_key", user.api_key)

    handler_chain = ApiKeyValidationHandler(users=users_repository).set_next(
        EmptyHandler()
    )

    handler_chain.handle(request)

    assert "api_key" in request.to_dict()
    assert request.get_attribute("api_key") == user.api_key
    assert len(request.logs) == 0


def test_api_key_validation_handler_without_api_key(
    users_repository: UserRepository, wallets_repository: WalletRepository
) -> None:
    request = ServiceRequest()

    handler = ApiKeyValidationHandler(users=users_repository)

    handler.handle(request)

    assert "api_key" not in request.to_dict()
    assert len(request.logs) == 1
    assert "API key validation skipped" in request.logs[0]


def test_api_key_validation_handler_non_existing_user(
    users_repository: UserRepository, wallets_repository: WalletRepository
) -> None:
    request = ServiceRequest()
    request.set_attribute("api_key", str(uuid4()))

    handler = ApiKeyValidationHandler(users=users_repository)

    with pytest.raises(UserDoesNotExistError):
        handler.handle(request)


def test_btc_conversion_handler_success(converter_mock: Converter) -> None:
    request = ServiceRequest()

    btc_conversion_handler = BtcConversionHandler(converter=converter_mock)

    btc_conversion_handler.handle(request)

    assert "exchange_rate" in request.to_dict()
    assert request.get_attribute("exchange_rate") == 40000
    assert len(request.logs) == 0


# ======================================================================================================================
#                                     WALLET SERVICE SPECIFIC HANDLER TESTS
# ======================================================================================================================


def test_wallet_count_handler_within_limit(
    wallets_repository: WalletRepository,
) -> None:
    user_id = uuid4()
    faker = FakeGenerator()
    wallets_repository.create(faker.generate_wallet(user_id))
    wallets_repository.create(faker.generate_wallet(user_id))

    request = ServiceRequest()
    request.set_attribute("api_key", user_id)

    wallet_count_handler = WalletCountHandler(wallets=wallets_repository)

    wallet_count_handler.handle(request)

    assert "api_key" in request.to_dict()
    assert len(request.logs) == 0


def test_wallet_count_handler_exceed_limit(
    wallets_repository: WalletRepository,
) -> None:
    user_id = uuid4()
    faker = FakeGenerator()
    wallets_repository.create(faker.generate_wallet(user_id))
    wallets_repository.create(faker.generate_wallet(user_id))
    wallets_repository.create(faker.generate_wallet(user_id))
    wallets_repository.create(faker.generate_wallet(user_id))

    request = ServiceRequest()
    request.set_attribute("api_key", user_id)

    wallet_count_handler = WalletCountHandler(wallets=wallets_repository)

    with pytest.raises(WalletLimitError):
        wallet_count_handler.handle(request)

    assert "api_key" in request.to_dict()


def test_wallet_count_handler_no_api_key(wallets_repository: WalletRepository) -> None:
    request = ServiceRequest()

    wallet_count_handler = WalletCountHandler(wallets=wallets_repository)

    wallet_count_handler.handle(request)

    assert "api_key" not in request.to_dict()
    assert len(request.logs) == 1
    assert "Wallet count skipped, no api_key provided" in request.logs[0]


def test_wallet_registration_handler_with_api_key(
    users_repository: UserRepository, wallets_repository: WalletRepository
) -> None:
    generator = FakeGenerator()
    user = generator.generate_user()
    users_repository.create(user)

    request = ServiceRequest()
    request.set_attribute("api_key", user.api_key)

    wallet_registration_handler = WalletRegistrationHandler(wallets=wallets_repository)

    wallet_registration_handler.handle(request)

    assert "api_key" in request.to_dict()
    assert len(request.logs) == 0
    assert "wallet_id" in request.to_dict()
    assert "wallet" in request.to_dict()

    assert wallets_repository.read(
        request.get_attribute("wallet_id")
    ) == request.get_attribute("wallet")


def test_wallet_registration_handler_no_api_key(
    users_repository: UserRepository, wallets_repository: WalletRepository
) -> None:
    request = ServiceRequest()

    wallet_registration_handler = WalletRegistrationHandler(wallets=wallets_repository)

    wallet_registration_handler.handle(request)

    assert "api_key" not in request.to_dict()
    assert len(request.logs) == 1
    assert "Wallet Registration skipped, no api_key provided" in request.logs[0]


def test_wallet_ownership_handler_valid_ownership(
    users_repository: UserRepository, wallets_repository: WalletRepository
) -> None:
    generator = FakeGenerator()
    user = generator.generate_user()
    wallet = generator.generate_wallet(user.api_key)
    users_repository.create(user)
    wallets_repository.create(wallet)

    request = ServiceRequest()
    request.set_attribute("api_key", user.api_key)
    request.set_attribute("wallet_id", wallet.wallet_address)

    wallet_ownership_handler = WalletOwnershipHandler(wallets=wallets_repository)

    wallet_ownership_handler.handle(request)

    assert "api_key" in request.to_dict()
    assert "wallet_id" in request.to_dict()
    assert len(request.logs) == 0


def test_wallet_ownership_handler_invalid_ownership(
    users_repository: UserRepository, wallets_repository: WalletRepository
) -> None:
    generator = FakeGenerator()
    user = generator.generate_user()
    wallet = generator.generate_wallet(user.api_key)
    users_repository.create(user)
    wallets_repository.create(wallet)

    # Create a request with the known API key and a different wallet ID
    request = ServiceRequest()
    request.set_attribute("api_key", user.api_key)
    request.set_attribute("wallet_id", str(uuid4()))  # Different wallet ID

    wallet_ownership_handler = WalletOwnershipHandler(wallets=wallets_repository)

    with pytest.raises(WalletOwnershipError):
        wallet_ownership_handler.handle(request)

    assert "api_key" in request.to_dict()
    assert "wallet_id" in request.to_dict()


def test_wallet_ownership_handler_skip_no_api_key(
    wallets_repository: WalletRepository,
) -> None:
    # Create a request without an API key
    request = ServiceRequest()
    request.set_attribute("wallet_id", str(uuid4()))

    wallet_ownership_handler = WalletOwnershipHandler(wallets=wallets_repository)

    wallet_ownership_handler.handle(request)

    assert "api_key" not in request.to_dict()
    assert "wallet_id" in request.to_dict()
    assert len(request.logs) == 1
    assert "Wallet ownership check skipped, no api_key provided" in request.logs[0]


def test_wallet_ownership_handler_skip_no_wallet_id(
    users_repository: UserRepository, wallets_repository: WalletRepository
) -> None:
    generator = FakeGenerator()
    user = generator.generate_user()
    users_repository.create(user)

    request = ServiceRequest()
    request.set_attribute("api_key", user.api_key)

    wallet_ownership_handler = WalletOwnershipHandler(wallets=wallets_repository)
    wallet_ownership_handler.handle(request)

    assert "api_key" in request.to_dict()
    assert "wallet_id" not in request.to_dict()
    assert len(request.logs) == 1
    assert "Wallet ownership check skipped, no wallet_id provided" in request.logs[0]


def test_wallet_fetch_handler_with_wallet_id(
    wallets_repository: WalletRepository,
) -> None:
    generator = FakeGenerator()
    wallet = generator.generate_wallet(uuid4())
    wallets_repository.create(wallet)

    request = ServiceRequest()
    request.set_attribute("wallet_id", wallet.wallet_address)

    wallet_fetch_handler = WalletFetchHandler(wallets=wallets_repository)

    wallet_fetch_handler.handle(request)

    assert "wallet" in request.to_dict()
    assert request.get_attribute("wallet") == wallet
    assert len(request.logs) == 0


def test_wallet_fetch_handler_without_wallet_id() -> None:
    request = ServiceRequest()

    wallet_fetch_handler = WalletFetchHandler(wallets=WalletInMemory())

    wallet_fetch_handler.handle(request)

    assert "wallet_id" not in request.to_dict()
    assert "wallet" not in request.to_dict()
    assert len(request.logs) == 1
    assert "Wallet fetch skipped, wallet_id was not provided" in request.logs[0]


def test_wallet_fetch_handler_with_non_existing_wallet_id(
    wallets_repository: WalletRepository,
) -> None:
    request = ServiceRequest()
    request.set_attribute("wallet_id", str(uuid4()))

    wallet_fetch_handler = WalletFetchHandler(wallets=wallets_repository)
    empty_handler = EmptyHandler()
    wallet_fetch_handler.set_next(empty_handler)

    with pytest.raises(WalletDoesNotExistError):
        wallet_fetch_handler.handle(request)


# ======================================================================================================================
#                                     TRANSACTION SERVICE SPECIFIC HANDLER TESTS
# ======================================================================================================================


def test_fee_handler_skip_calculation_missing_attributes(
    wallets_repository: WalletRepository,
) -> None:
    request = ServiceRequest()

    fee_handler = FeeHandler(wallets=wallets_repository)

    fee_handler.handle(request)

    assert "fee" not in request.to_dict()
    assert len(request.logs) == 1
    assert "Fee calculation skipped, missing required attributes" in request.logs[0]


def test_fee_handler_skip_calculation_sender_not_owned(
    wallets_repository: WalletRepository,
) -> None:
    generator = FakeGenerator()
    user = generator.generate_user()
    recipient_wallet = generator.generate_wallet(user.api_key)

    wallets_repository.create(recipient_wallet)

    request = ServiceRequest()
    request.set_attribute("api_key", user.api_key)
    request.set_attribute("sender_wallet_id", str(uuid4()))
    request.set_attribute("recipient_wallet_id", recipient_wallet.wallet_address)

    fee_handler = FeeHandler(wallets=wallets_repository)

    with pytest.raises(WalletOwnershipError):
        fee_handler.handle(request)

    assert "fee" not in request.to_dict()


def test_fee_handler_fee_calculation_recipient_not_owned(
    wallets_repository: WalletRepository,
) -> None:
    generator = FakeGenerator()
    user = generator.generate_user()
    sender_wallet = generator.generate_wallet(user.api_key)

    wallets_repository.create(sender_wallet)

    request = ServiceRequest()
    request.set_attribute("api_key", user.api_key)
    request.set_attribute("sender_wallet_id", sender_wallet.wallet_address)
    request.set_attribute("recipient_wallet_id", str(uuid4()))

    fee_handler = FeeHandler(wallets=wallets_repository)

    fee_handler.handle(request)

    assert "fee" in request.to_dict()
    assert request.get_attribute("fee") == 0.015


def test_fee_handler_no_fee_calculation_both_owned(
    wallets_repository: WalletRepository,
) -> None:
    generator = FakeGenerator()
    user = generator.generate_user()
    sender_wallet = generator.generate_wallet(user.api_key)
    recipient_wallet = generator.generate_wallet(user.api_key)

    wallets_repository.create(sender_wallet)
    wallets_repository.create(recipient_wallet)

    request = ServiceRequest()
    request.set_attribute("api_key", user.api_key)
    request.set_attribute("sender_wallet_id", sender_wallet.wallet_address)
    request.set_attribute("recipient_wallet_id", recipient_wallet.wallet_address)

    fee_handler = FeeHandler(wallets=wallets_repository)

    fee_handler.handle(request)

    assert "fee" in request.to_dict()
    assert request.get_attribute("fee") == 0


def test_wallet_existence_handler_skip_check_missing_wallet_ids(
    wallets_repository: WalletRepository,
) -> None:
    request = ServiceRequest()

    wallet_existence_handler = WalletExistenceHandler(wallets=wallets_repository)

    wallet_existence_handler.handle(request)

    assert "sender_wallet" not in request.to_dict()
    assert "recipient_wallet" not in request.to_dict()
    assert len(request.logs) == 1
    assert "Wallet existence check skipped, wallet_ids not provided" in request.logs[0]


def test_wallet_existence_handler_wallet_does_not_exist_sender(
    wallets_repository: WalletRepository,
) -> None:
    generator = FakeGenerator()
    recipient_wallet = generator.generate_wallet(uuid4())

    wallets_repository.create(recipient_wallet)

    request = ServiceRequest()
    request.set_attribute("sender_wallet_id", str(uuid4()))
    request.set_attribute("recipient_wallet_id", recipient_wallet.wallet_address)

    wallet_existence_handler = WalletExistenceHandler(wallets=wallets_repository)

    with pytest.raises(WalletDoesNotExistError):
        wallet_existence_handler.handle(request)

    assert "sender_wallet" not in request.to_dict()
    assert "recipient_wallet" not in request.to_dict()
    assert len(request.logs) == 1
    assert "Sender wallet does not exist" in request.logs[0]


def test_wallet_existence_handler_wallet_does_not_exist_recipient(
    wallets_repository: WalletRepository,
) -> None:
    generator = FakeGenerator()
    sender_wallet = generator.generate_wallet(uuid4())

    wallets_repository.create(sender_wallet)

    request = ServiceRequest()
    request.set_attribute("sender_wallet_id", sender_wallet.wallet_address)
    request.set_attribute("recipient_wallet_id", str(uuid4()))

    wallet_existence_handler = WalletExistenceHandler(wallets=wallets_repository)

    with pytest.raises(WalletDoesNotExistError):
        wallet_existence_handler.handle(request)

    assert "sender_wallet" not in request.to_dict()
    assert "recipient_wallet" not in request.to_dict()
    assert len(request.logs) == 1
    assert "Recipient wallet does not exist" in request.logs[0]


def test_wallet_existence_handler_successful_check(
    wallets_repository: WalletRepository,
) -> None:
    generator = FakeGenerator()
    sender_wallet = generator.generate_wallet(uuid4())
    recipient_wallet = generator.generate_wallet(uuid4())

    wallets_repository.create(sender_wallet)
    wallets_repository.create(recipient_wallet)

    request = ServiceRequest()
    request.set_attribute("sender_wallet_id", sender_wallet.wallet_address)
    request.set_attribute("recipient_wallet_id", recipient_wallet.wallet_address)

    wallet_existence_handler = WalletExistenceHandler(wallets=wallets_repository)

    wallet_existence_handler.handle(request)

    assert "sender_wallet" in request.to_dict()
    assert request.get_attribute("sender_wallet") == sender_wallet
    assert "recipient_wallet" in request.to_dict()
    assert request.get_attribute("recipient_wallet") == recipient_wallet
    assert len(request.logs) == 0


def test_balance_check_handler_skip_missing_attributes(
    wallets_repository: WalletInMemory,
) -> None:
    request = ServiceRequest()

    balance_check_handler = BalanceCheckHandler()

    balance_check_handler.handle(request)

    assert len(request.logs) == 1
    assert "Balance check skipped, missing required attributes" in request.logs[0]


def test_balance_check_handler_negative_transaction_amount(
    wallets_repository: WalletInMemory,
) -> None:
    sender_wallet = Wallet(wallet_address=uuid4(), btc_balance=1.0, user_id=uuid4())
    request = ServiceRequest()
    request.set_attribute("sender_wallet", sender_wallet)
    request.set_attribute("amount_btc", -0.5)  # Negative transaction amount

    balance_check_handler = BalanceCheckHandler()

    with pytest.raises(BadRequestError):
        balance_check_handler.handle(request)

    assert len(request.logs) == 0


def test_balance_check_handler_insufficient_balance(
    wallets_repository: WalletInMemory,
) -> None:
    sender_wallet = Wallet(wallet_address=uuid4(), btc_balance=1.0, user_id=uuid4())

    request = ServiceRequest()
    request.set_attribute("sender_wallet", sender_wallet)
    request.set_attribute("amount_btc", 2.0)
    request.set_attribute("fee", 0.1)

    balance_check_handler = BalanceCheckHandler()

    with pytest.raises(InsufficientBalanceError):
        balance_check_handler.handle(request)

    assert len(request.logs) == 0


def test_balance_check_handler_sufficient_balance(
    wallets_repository: WalletInMemory,
) -> None:
    sender_wallet = Wallet(wallet_address=uuid4(), btc_balance=1, user_id=uuid4())

    request = ServiceRequest()
    request.set_attribute("sender_wallet", sender_wallet)
    request.set_attribute("amount_btc", 0.5)
    request.set_attribute("fee", 0.1)

    balance_check_handler = BalanceCheckHandler()

    balance_check_handler.handle(request)

    assert len(request.logs) == 0


def test_transaction_execution_handler_skip_missing_attributes(
    wallets_repository: WalletInMemory,
    transactions_repository: TransactionRepository,
    system: System,
) -> None:
    request = ServiceRequest()

    transaction_execution_handler = TransactionExecutionHandler(
        wallets=wallets_repository, transactions=transactions_repository, system=system
    )

    transaction_execution_handler.handle(request)

    assert len(request.logs) == 1
    assert (
        "Transaction execution skipped, missing required attributes" in request.logs[0]
    )


def test_transaction_execution_handler_successful_execution(
    wallets_repository: WalletRepository,
    transactions_repository: TransactionRepository,
    system: System,
) -> None:
    sender_wallet = Wallet(wallet_address=uuid4(), btc_balance=2.0, user_id=uuid4())
    recipient_wallet = Wallet(wallet_address=uuid4(), btc_balance=1.0, user_id=uuid4())

    wallets_repository.create(sender_wallet)
    wallets_repository.create(recipient_wallet)

    request = ServiceRequest()
    request.set_attribute("sender_wallet", sender_wallet)
    request.set_attribute("recipient_wallet", recipient_wallet)
    request.set_attribute("amount_btc", 1.0)
    request.set_attribute("fee", 0.1)

    transaction_execution_handler = TransactionExecutionHandler(
        wallets=wallets_repository, transactions=transactions_repository, system=system
    )

    transaction_execution_handler.handle(request)

    assert len(request.logs) == 0

    updated_sender_wallet = wallets_repository.read(sender_wallet.wallet_address)
    updated_recipient_wallet = wallets_repository.read(recipient_wallet.wallet_address)

    assert updated_sender_wallet.btc_balance == 2.0 - 1.0 * (1 + 0.1)
    assert updated_recipient_wallet.btc_balance == 2.0

    created_transaction = transactions_repository.read(
        request.get_attribute("transaction").transaction_id
    )
    assert created_transaction.sender_wallet_id == sender_wallet.wallet_address
    assert created_transaction.recipient_wallet_id == recipient_wallet.wallet_address
    assert created_transaction.amount_btc == 1.0
    assert created_transaction.fee == 0.1
    assert created_transaction.timestamp <= datetime.utcnow()

    assert system.get_platform_profit() == 0.1 * 1.0


def test_wallet_addresses_handler_successful_retrieval(
    wallets_repository: WalletInMemory,
) -> None:
    user_id = uuid4()
    generator = FakeGenerator()
    wallet1 = generator.generate_wallet(user_id=user_id)
    wallet2 = generator.generate_wallet(user_id=user_id)

    wallets_repository.create(wallet1)
    wallets_repository.create(wallet2)

    request = ServiceRequest()
    request.set_attribute("api_key", user_id)

    wallet_addresses_handler = WalletAddressesHandler(wallets=wallets_repository)

    wallet_addresses_handler.handle(request)

    assert "wallet_ids" in request.to_dict()
    assert request.get_attribute("wallet_ids") == [
        wallet1.wallet_address,
        wallet2.wallet_address,
    ]


def test_wallet_addresses_handler_skip_no_api_key(
    wallets_repository: WalletInMemory,
) -> None:
    request = ServiceRequest()

    wallet_addresses_handler = WalletAddressesHandler(wallets=wallets_repository)

    wallet_addresses_handler.handle(request)

    assert "wallet_ids" not in request.to_dict()
    assert len(request.logs) == 1
    assert "Wallet addresses retrieval skipped, no api_key provided" in request.logs[0]


def test_fetch_withdrawals_handler_successful_fetch(
    transactions_repository: TransactionInMemory,
) -> None:
    wallet_id = uuid4()
    generator = FakeGenerator()
    withdrawal_transaction = generator.generate_transaction(wallet_id, uuid4())
    transactions_repository.create(withdrawal_transaction)

    request = ServiceRequest()
    request.set_attribute("wallet_ids", [wallet_id])

    fetch_withdrawals_handler = FetchWithdrawalsHandler(
        transactions=transactions_repository
    )

    fetch_withdrawals_handler.handle(request)

    assert "performed_transactions" in request.to_dict()
    assert len(request.get_attribute("performed_transactions")) == 1
    assert request.get_attribute("performed_transactions")[0] == withdrawal_transaction


def test_fetch_withdrawals_handler_skip_no_wallet_ids(
    transactions_repository: TransactionInMemory,
) -> None:
    request = ServiceRequest()

    fetch_withdrawals_handler = FetchWithdrawalsHandler(
        transactions=transactions_repository
    )

    fetch_withdrawals_handler.handle(request)

    assert "performed_transactions" not in request.to_dict()
    assert len(request.logs) == 1
    assert (
        "Fetching withdrawals skipped, missing required wallet_ids" in request.logs[0]
    )


def test_fetch_deposits_handler_successful_fetch(
    transactions_repository: TransactionInMemory,
) -> None:
    wallet_id = uuid4()
    generator = FakeGenerator()
    deposit_transaction = generator.generate_transaction(uuid4(), wallet_id)
    transactions_repository.create(deposit_transaction)

    request = ServiceRequest()
    request.set_attribute("wallet_ids", [wallet_id])

    fetch_deposits_handler = FetchDepositsHandler(transactions=transactions_repository)

    fetch_deposits_handler.handle(request)

    assert "performed_transactions" in request.to_dict()
    assert len(request.get_attribute("performed_transactions")) == 1
    assert request.get_attribute("performed_transactions")[0] == deposit_transaction


def test_fetch_deposits_handler_skip_no_wallet_ids(
    transactions_repository: TransactionInMemory,
) -> None:
    request = ServiceRequest()

    fetch_deposits_handler = FetchDepositsHandler(transactions=transactions_repository)
    empty_handler = EmptyHandler()
    fetch_deposits_handler.set_next(empty_handler)

    fetch_deposits_handler.handle(request)

    assert "performed_transactions" not in request.to_dict()
    assert len(request.logs) == 1
    assert "Fetching deposits skipped, missing required wallet_ids" in request.logs[0]


# ======================================================================================================================
#                                      SYSTEM SERVICE SPECIFIC HANDLER TESTS
# ======================================================================================================================


def test_is_admin_handler_successful_validation(system: SystemInMemory) -> None:
    admin_key = system.get_admin_key()

    request = ServiceRequest()
    request.set_attribute("api_key", admin_key)

    is_admin_handler = IsAdminHandler(system=system)

    is_admin_handler.handle(request)

    assert len(request.logs) == 0


def test_is_admin_handler_unsuccessful_validation(system: SystemInMemory) -> None:
    request = ServiceRequest()
    request.set_attribute("api_key", uuid4())

    is_admin_handler = IsAdminHandler(system=system)

    with pytest.raises(ForbiddenError):
        is_admin_handler.handle(request)


def test_is_admin_handler_skip_no_api_key(system: SystemInMemory) -> None:
    request = ServiceRequest()

    is_admin_handler = IsAdminHandler(system=system)

    is_admin_handler.handle(request)

    assert len(request.logs) == 1
    assert "admin key validation skipped, no api_key provided" in request.logs[0]


def test_get_statistics_handler_successful_retrieval(
    transactions_repository: TransactionInMemory, system: SystemInMemory
) -> None:
    total_transactions = 5
    platform_profit = 100.0
    generator = FakeGenerator()

    for _ in range(total_transactions):
        trans = generator.generate_transaction(uuid4(), uuid4())
        transactions_repository.create(trans)
        system.add_profitable_transaction(trans.transaction_id, 20)

    request = ServiceRequest()

    get_statistics_handler = GetStatisticsHandler(
        system=system, transactions=transactions_repository
    )

    get_statistics_handler.handle(request)

    assert "total_transactions" in request.to_dict()
    assert request.get_attribute("total_transactions") == total_transactions
    assert "platform_profit" in request.to_dict()
    assert request.get_attribute("platform_profit") == platform_profit


def test_get_statistics_handler_skip_no_data(
    transactions_repository: TransactionInMemory, system: SystemInMemory
) -> None:
    request = ServiceRequest()

    get_statistics_handler = GetStatisticsHandler(
        system=system, transactions=transactions_repository
    )

    get_statistics_handler.handle(request)

    assert "total_transactions" in request.to_dict()
    assert request.get_attribute("total_transactions") == 0
    assert "platform_profit" in request.to_dict()
    assert request.get_attribute("platform_profit") == 0.0
