from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol
from uuid import UUID, uuid4


@dataclass
class User:
    email: str
    password: str
    api_key: UUID = field(default_factory=uuid4)


class UserRepository(Protocol):
    def create(self, user: User) -> None:
        pass

    def read(self, user_id: UUID) -> User:
        pass

    def update(self, user: User) -> None:
        pass

    def delete(self, user_id: UUID) -> None:
        pass

    def read_all(self) -> list[User]:
        pass
