from dataclasses import dataclass
from uuid import UUID

from passlib.handlers.bcrypt import bcrypt

from core.errors import UserDoesNotExistError
from core.users.repository import User, UserRepository


@dataclass
class UserService:
    users: UserRepository

    def register_user(self, email: str, password: str) -> User:
        self._validate_email(email)
        hashed_password = self._hash_password(password)
        new_user = User(email=email, password=hashed_password)
        self.users.create(new_user)
        return new_user

    def _validate_email(self, email: str) -> None:
        if not email or "@" not in email or "." not in email:
            raise ValueError("Invalid email address")

    def _hash_password(self, password: str) -> str:
        return str(bcrypt.hash(password))

    def fetch_user(self, api_key: UUID) -> User:
        try:
            return self.users.read(api_key)
        except UserDoesNotExistError as e:
            raise e

    def fetch_all_units(self) -> list[User]:
        return self.users.read_all()
