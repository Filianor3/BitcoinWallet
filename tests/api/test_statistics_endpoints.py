import os
from uuid import uuid4

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

from core.users.repository import User
from core.wallets.repository import Wallet
from runner.setup import init_test_app
from tests.fake import FakeGenerator

fake_generator = FakeGenerator()
load_dotenv()


@pytest.fixture
def client() -> TestClient:
    return TestClient(init_test_app())


@pytest.fixture
def registered_user_a(client: TestClient) -> User:
    registration_request = fake_generator.generate_registration_request()
    response = client.post("/users", json=registration_request)
    user = User(
        email=registration_request["email"],
        password=registration_request["password"],
        api_key=response.json()["api_key"],
    )
    return user


@pytest.fixture
def registered_user_b(client: TestClient) -> User:
    registration_request = fake_generator.generate_registration_request()
    response = client.post("/users", json=registration_request)
    user = User(
        email=registration_request["email"],
        password=registration_request["password"],
        api_key=response.json()["api_key"],
    )
    return user


@pytest.fixture
def wallet_a1(client: TestClient, registered_user_a: User) -> Wallet:
    response = client.post(
        "/wallets", headers={"X_API-KEY": str(registered_user_a.api_key)}
    )
    wallet = response.json()["wallet"]
    return Wallet(
        wallet_address=wallet["wallet_address"],
        user_id=registered_user_a.api_key,
        btc_balance=wallet["balance_btc"],
    )


@pytest.fixture
def wallet_a2(client: TestClient, registered_user_a: User) -> Wallet:
    response = client.post(
        "/wallets", headers={"X_API-KEY": str(registered_user_a.api_key)}
    )
    wallet = response.json()["wallet"]
    return Wallet(
        wallet_address=wallet["wallet_address"],
        user_id=registered_user_a.api_key,
        btc_balance=wallet["balance_btc"],
    )


@pytest.fixture
def wallet_b(client: TestClient, registered_user_b: User) -> Wallet:
    response = client.post(
        "/wallets", headers={"X_API-KEY": str(registered_user_b.api_key)}
    )
    wallet = response.json()["wallet"]
    return Wallet(
        wallet_address=wallet["wallet_address"],
        user_id=registered_user_b.api_key,
        btc_balance=wallet["balance_btc"],
    )


def test_statistics_no_transactions(
    client: TestClient,
) -> None:
    admin_key_str = os.getenv("ADMIN_KEY")
    response = client.get("/statistics", headers={"X_API-KEY": str(admin_key_str)})

    assert response.status_code == 200
    assert "total_transactions" in response.json()
    assert "platform_profit" in response.json()

    total_transactions = response.json()["total_transactions"]
    platform_profit = response.json()["platform_profit"]

    assert total_transactions == 0
    assert platform_profit == 0


def test_statistics_endpoint_no_fee_transactions(
    client: TestClient,
    registered_user_a: User,
    wallet_a1: Wallet,
    wallet_a2: Wallet,
) -> None:
    transaction_request_1 = fake_generator.generate_transaction_request(
        sender_wallet_id=wallet_a1.wallet_address,
        recipient_wallet_id=wallet_a2.wallet_address,
        amount=0.1,
    )
    transaction_request_2 = fake_generator.generate_transaction_request(
        sender_wallet_id=wallet_a1.wallet_address,
        recipient_wallet_id=wallet_a2.wallet_address,
        amount=0.05,
    )

    client.post(
        "/transactions",
        json=transaction_request_1,
        headers={"X_API-KEY": str(registered_user_a.api_key)},
    )
    client.post(
        "/transactions",
        json=transaction_request_2,
        headers={"X_API-KEY": str(registered_user_a.api_key)},
    )

    admin_key_str = os.getenv("ADMIN_KEY")
    response = client.get("/statistics", headers={"X_API-KEY": str(admin_key_str)})

    assert response.status_code == 200
    assert "total_transactions" in response.json()
    assert "platform_profit" in response.json()

    total_transactions = response.json()["total_transactions"]
    platform_profit = response.json()["platform_profit"]

    assert total_transactions == 2
    assert platform_profit == 0


def test_statistics_endpoint_transactions_with_fees(
    client: TestClient,
    registered_user_a: User,
    wallet_a1: Wallet,
    wallet_b: Wallet,
) -> None:
    amount_1 = 0.2
    amount_2 = 0.3
    transaction_request_1 = fake_generator.generate_transaction_request(
        sender_wallet_id=wallet_a1.wallet_address,
        recipient_wallet_id=wallet_b.wallet_address,
        amount=amount_1,
    )
    transaction_request_2 = fake_generator.generate_transaction_request(
        sender_wallet_id=wallet_a1.wallet_address,
        recipient_wallet_id=wallet_b.wallet_address,
        amount=amount_2,
    )

    client.post(
        "/transactions",
        json=transaction_request_1,
        headers={"X_API-KEY": str(registered_user_a.api_key)},
    )
    client.post(
        "/transactions",
        json=transaction_request_2,
        headers={"X_API-KEY": str(registered_user_a.api_key)},
    )

    admin_key_str = os.getenv("ADMIN_KEY")
    response = client.get("/statistics", headers={"X_API-KEY": str(admin_key_str)})

    assert response.status_code == 200
    assert "total_transactions" in response.json()
    assert "platform_profit" in response.json()

    total_transactions = response.json()["total_transactions"]
    platform_profit = response.json()["platform_profit"]

    assert total_transactions == 2
    assert platform_profit == (amount_1 + amount_2) * 0.015


def test_statistics_wrong_admin_key(
    client: TestClient,
) -> None:
    admin_key_str = str(uuid4())
    print("ADMIN KEY:")
    print(admin_key_str)
    response = client.get("/statistics", headers={"X_API-KEY": str(admin_key_str)})

    assert response.status_code == 403
    assert "message" in response.json()
    assert response.json()["message"] == "Only admin can access statistics."
