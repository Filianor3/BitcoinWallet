from uuid import uuid4

import pytest

from core.errors import DoesNotExistError, ExistsError
from core.users.repository import UserRepository

# from infra.repositories.inmemory.users_inmemory import UserInMemory
from infra.repositories.sqlite.db_manager import DbManager
from tests.fake import FakeGenerator


@pytest.fixture
def repository() -> UserRepository:
    db_manager = DbManager(db_name="test_db")
    db_manager.drop_tables()
    db_manager.create_tables()
    return db_manager.get_user_repository()
    # return SQLiteUsers("test_db")


def test_should_not_read_unknown(repository: UserRepository) -> None:
    unknown_id = uuid4()

    with pytest.raises(DoesNotExistError):
        repository.read(unknown_id)


def test_should_persist(repository: UserRepository) -> None:
    user = FakeGenerator().generate_user()

    repository.create(user)

    assert repository.read(user.api_key) == user


def test_should_not_duplicate(repository: UserRepository) -> None:
    user = FakeGenerator().generate_user()
    repository.create(user)

    with pytest.raises(ExistsError):
        repository.create(user)


def test_should_not_update_unknown(repository: UserRepository) -> None:
    user = FakeGenerator().generate_user()

    with pytest.raises(DoesNotExistError):
        repository.update(user)


def test_should_persist_update(repository: UserRepository) -> None:
    user = FakeGenerator().generate_user()
    repository.create(user)

    user.email = "updated@example.com"
    user.password = "updatedpassword456"

    repository.update(user)

    assert repository.read(user.api_key) == user


def test_should_read_all(repository: UserRepository) -> None:
    user1 = FakeGenerator().generate_user()
    user2 = FakeGenerator().generate_user()
    repository.create(user1)
    repository.create(user2)

    users = repository.read_all()

    assert len(users) == 2
    assert user1 in users
    assert user2 in users


def test_should_read_all_empty(repository: UserRepository) -> None:
    users = repository.read_all()

    assert len(users) == 0
