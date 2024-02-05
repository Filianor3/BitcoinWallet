import sqlite3
from dataclasses import dataclass
from uuid import UUID

from core.errors import UserDoesNotExistError, UserExistsError
from core.users.repository import User, UserRepository


@dataclass
class SQLiteUsers(UserRepository):
    db_name: str

    def create(self, user: User) -> None:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            # Check if user with the same email already exists
            cursor.execute("SELECT 1 FROM users WHERE email = ?", (user.email,))
            existing_user = cursor.fetchone()
            if existing_user:
                raise UserExistsError(f"User with email <{user.email}> already exists")

            # Insert user into the 'users' table
            cursor.execute(
                "INSERT INTO users (id, email, password) VALUES (?, ?, ?)",
                (str(user.api_key), user.email, user.password),
            )

    def read(self, user_id: UUID) -> User:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            # Retrieve user from the 'users' table
            cursor.execute(
                "SELECT id, email, password FROM users WHERE id = ?", (str(user_id),)
            )
            result = cursor.fetchone()

            if result:
                return User(
                    api_key=UUID(result[0]), email=result[1], password=result[2]
                )
            else:
                raise UserDoesNotExistError(f"User with id <{user_id}> does not exist")

    def update(self, user: User) -> None:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            # Check if the user with the given id exists
            cursor.execute("SELECT 1 FROM users WHERE id = ?", (str(user.api_key),))
            existing_user = cursor.fetchone()
            if existing_user:
                # Update user in the 'users' table
                cursor.execute(
                    "UPDATE users SET email = ?, password = ? WHERE id = ?",
                    (user.email, user.password, str(user.api_key)),
                )
            else:
                raise UserDoesNotExistError(f"User with ID <{user.api_key}> not found")

    def delete(self, user_id: UUID) -> None:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            # Check if the user with the given id exists
            cursor.execute("SELECT 1 FROM users WHERE id = ?", (str(user_id),))
            existing_user = cursor.fetchone()
            if existing_user:
                # Delete user from the 'users' table
                cursor.execute("DELETE FROM users WHERE id = ?", (str(user_id),))
            else:
                raise UserDoesNotExistError(f"User with id <{user_id}> does not exist")

    def read_all(self) -> list[User]:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            # Retrieve all users from the 'users' table
            cursor.execute("SELECT id, email, password FROM users")
            results = cursor.fetchall()

            return [
                User(api_key=UUID(result[0]), email=result[1], password=result[2])
                for result in results
            ]
