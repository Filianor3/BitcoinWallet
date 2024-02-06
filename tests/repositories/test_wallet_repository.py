from uuid import uuid4

import pytest

from core.errors import DoesNotExistError, ExistsError
from core.wallets.repository import WalletRepository

# from infra.repositories.inmemory.wallets_inmemory import WalletInMemory
from infra.repositories.sqlite.db_manager import DbManager
from tests.fake import FakeGenerator


@pytest.fixture
def repository() -> WalletRepository:
    # return WalletInMemory()
    db_manager = DbManager(db_name="test_db")
    db_manager.drop_tables()
    db_manager.create_tables()
    return db_manager.get_wallet_repository()


def test_should_not_read_unknown(repository: WalletRepository) -> None:
    unknown_id = uuid4()

    with pytest.raises(DoesNotExistError):
        repository.read(unknown_id)


def test_should_persist(repository: WalletRepository) -> None:
    wallet = FakeGenerator().generate_wallet(uuid4())

    repository.create(wallet)

    assert repository.read(wallet.wallet_address) == wallet


def test_should_not_duplicate(repository: WalletRepository) -> None:
    wallet = FakeGenerator().generate_wallet(uuid4())
    repository.create(wallet)

    with pytest.raises(ExistsError):
        repository.create(wallet)


def test_should_not_update_unknown(repository: WalletRepository) -> None:
    wallet = FakeGenerator().generate_wallet(uuid4())

    with pytest.raises(DoesNotExistError):
        repository.update(wallet)


def test_should_persist_update(repository: WalletRepository) -> None:
    wallet = FakeGenerator().generate_wallet(uuid4())
    repository.create(wallet)

    wallet.btc_balance = 2.0

    repository.update(wallet)

    assert repository.read(wallet.wallet_address).btc_balance == 2.0


def test_should_read_all(repository: WalletRepository) -> None:
    wallet1 = FakeGenerator().generate_wallet(uuid4())
    wallet2 = FakeGenerator().generate_wallet(uuid4())
    repository.create(wallet1)
    repository.create(wallet2)

    wallets = repository.read_all()

    assert len(wallets) == 2
    assert wallet1 in wallets
    assert wallet2 in wallets


def test_should_read_all_empty(repository: WalletRepository) -> None:
    wallets = repository.read_all()

    assert len(wallets) == 0


def test_read_user_wallets_unknown_user(repository: WalletRepository) -> None:
    unknown_user_id = uuid4()

    wallets = repository.read_user_wallets(unknown_user_id)

    assert len(wallets) == 0


def test_read_user_wallets_with_wallets(repository: WalletRepository) -> None:
    user_id = uuid4()
    wallet1 = FakeGenerator().generate_wallet(user_id)
    wallet2 = FakeGenerator().generate_wallet(user_id)

    repository.create(wallet1)
    repository.create(wallet2)

    wallets = repository.read_user_wallets(user_id)

    assert len(wallets) == 2
    assert wallet1 in wallets
    assert wallet2 in wallets
