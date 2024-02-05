from uuid import uuid4

import pytest

from core.errors import DoesNotExistError, ExistsError
from core.transactions.repository import TransactionRepository

# from infra.repositories.inmemory.transactions_inmemory import TransactionInMemory
from infra.repositories.sqlite.db_manager import DbManager
from tests.fake import FakeGenerator


@pytest.fixture
def repository() -> TransactionRepository:
    db_manager = DbManager(db_name="test_db")
    db_manager.drop_tables()
    db_manager.create_tables()
    return db_manager.get_transaction_repository()
    # return TransactionInMemory()


def test_should_not_read_unknown(repository: TransactionRepository) -> None:
    unknown_id = uuid4()

    with pytest.raises(DoesNotExistError):
        repository.read(unknown_id)


def test_should_persist(repository: TransactionRepository) -> None:
    generator = FakeGenerator()
    transaction = generator.generate_transaction(uuid4(), uuid4())

    repository.create(transaction)

    assert repository.read(transaction.transaction_id) == transaction


def test_should_not_duplicate(repository: TransactionRepository) -> None:
    generator = FakeGenerator()
    transaction = generator.generate_transaction(uuid4(), uuid4())
    repository.create(transaction)

    with pytest.raises(ExistsError):
        repository.create(transaction)


def test_should_not_update_unknown(repository: TransactionRepository) -> None:
    generator = FakeGenerator()
    transaction = generator.generate_transaction(uuid4(), uuid4())

    with pytest.raises(DoesNotExistError):
        repository.update(transaction)


def test_should_persist_update(repository: TransactionRepository) -> None:
    generator = FakeGenerator()
    transaction = generator.generate_transaction(uuid4(), uuid4())
    repository.create(transaction)

    transaction.amount_btc = 2.0
    repository.update(transaction)

    assert repository.read(transaction.transaction_id).amount_btc == 2.0


def test_should_read_all(repository: TransactionRepository) -> None:
    generator = FakeGenerator()
    transaction1 = generator.generate_transaction(uuid4(), uuid4())
    transaction2 = generator.generate_transaction(uuid4(), uuid4())
    repository.create(transaction1)
    repository.create(transaction2)

    transactions = repository.read_all()

    assert len(transactions) == 2
    assert transaction1 in transactions
    assert transaction2 in transactions


def test_should_read_all_empty(repository: TransactionRepository) -> None:
    transactions = repository.read_all()

    assert len(transactions) == 0


def test_should_delete_transaction(repository: TransactionRepository) -> None:
    generator = FakeGenerator()
    transaction = generator.generate_transaction(uuid4(), uuid4())
    repository.create(transaction)

    repository.delete(transaction.transaction_id)

    with pytest.raises(DoesNotExistError):
        repository.read(transaction.transaction_id)


def test_read_wallet_withdrawals(repository: TransactionRepository) -> None:
    generator = FakeGenerator()
    wallet_id = uuid4()

    transaction1 = generator.generate_transaction(wallet_id, uuid4())
    transaction2 = generator.generate_transaction(wallet_id, uuid4())
    transaction3 = generator.generate_transaction(uuid4(), uuid4())

    repository.create(transaction1)
    repository.create(transaction2)
    repository.create(transaction3)

    withdrawals = repository.read_wallet_withdrawals(wallet_id)

    assert len(withdrawals) == 2
    assert transaction1 in withdrawals
    assert transaction2 in withdrawals
    assert transaction3 not in withdrawals


def test_read_wallet_deposits(repository: TransactionRepository) -> None:
    generator = FakeGenerator()
    wallet_id = uuid4()

    transaction1 = generator.generate_transaction(uuid4(), wallet_id)
    transaction2 = generator.generate_transaction(uuid4(), wallet_id)
    transaction3 = generator.generate_transaction(uuid4(), uuid4())

    repository.create(transaction1)
    repository.create(transaction2)
    repository.create(transaction3)

    deposits = repository.read_wallet_deposits(wallet_id)

    assert len(deposits) == 2
    assert transaction1 in deposits
    assert transaction2 in deposits
    assert transaction3 not in deposits


def test_transaction_deletion_with_invalid_id(
    repository: TransactionRepository,
) -> None:
    unknown_id = uuid4()

    with pytest.raises(DoesNotExistError):
        repository.delete(unknown_id)
