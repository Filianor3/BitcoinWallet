from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from faker import Faker

from core.transactions.repository import Transaction
from core.users.repository import User
from core.wallets.repository import Wallet


@dataclass
class FakeGenerator:
    faker: Faker = field(default_factory=Faker)

    def generate_user(self) -> User:
        return User(
            email=self.faker.email(), password=self.faker.password(), api_key=uuid4()
        )

    def generate_wallet(self, user_id: UUID) -> Wallet:
        return Wallet(
            user_id=user_id,
            btc_balance=self.faker.pyfloat(min_value=0, max_value=10),
            wallet_address=uuid4(),
        )

    def generate_transaction(
        self, sender_wallet_id: UUID, recipient_wallet_id: UUID
    ) -> Transaction:
        return Transaction(
            transaction_id=uuid4(),
            sender_wallet_id=sender_wallet_id,
            recipient_wallet_id=recipient_wallet_id,
            amount_btc=self.faker.pyfloat(min_value=0, max_value=10),
            fee=self.faker.pyfloat(min_value=0, max_value=1),
            timestamp=datetime.utcnow(),
        )

    def generate_registration_request(self) -> dict[str, Any]:
        user = self.generate_user()
        return {"email": user.email, "password": user.password}

    def generate_wallet_creation_request(
        self, api_key: Optional[UUID] = None
    ) -> dict[str, Any]:
        return {
            "X_API-KEY": str(api_key) if api_key else str(self.generate_user().api_key)
        }

    def generate_transaction_request(
        self, sender_wallet_id: UUID, recipient_wallet_id: UUID, amount: float
    ) -> dict[str, Any]:
        return {
            "sender_wallet_id": str(sender_wallet_id),
            "recipient_wallet_id": str(recipient_wallet_id),
            "amount_btc": amount,
        }
