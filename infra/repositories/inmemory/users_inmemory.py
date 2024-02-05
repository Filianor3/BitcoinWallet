from dataclasses import dataclass, field
from uuid import UUID

from core.errors import UserDoesNotExistError, UserExistsError
from core.users.repository import User, UserRepository


@dataclass
class UserInMemory(UserRepository):
    users: dict[UUID, User] = field(default_factory=dict)

    def create(self, user: User) -> None:
        # Check if user with the same email already exists
        if any(
            existing_user.email == user.email for existing_user in self.users.values()
        ):
            raise UserExistsError(f"User with email <{user.email}> already exists")

        self.users[user.api_key] = user

    def read(self, user_id: UUID) -> User:
        try:
            return self.users[user_id]
        except KeyError:
            raise UserDoesNotExistError(f"User with id <{user_id}> does not exist")

    def update(self, user: User) -> None:
        if user.api_key in self.users:
            self.users[user.api_key] = user
        else:
            raise UserDoesNotExistError(f"User with ID <{user.api_key}> not found")

    def delete(self, user_id: UUID) -> None:
        try:
            del self.users[user_id]
        except KeyError:
            raise UserDoesNotExistError(f"Unit with id <{user_id}> does not exist")

    def read_all(self) -> list[User]:
        return list(self.users.values())
