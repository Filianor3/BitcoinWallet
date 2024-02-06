from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from core.users.repository import User
from core.wallets.repository import Wallet
from runner.setup import init_test_app
from tests.fake import FakeGenerator

fake_generator = FakeGenerator()


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
def sender_wallet_a(client: TestClient, registered_user_a: User) -> Wallet:
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
def recipient_wallet_a(client: TestClient, registered_user_a: User) -> Wallet:
    response = client.post(
        "/wallets",
        headers={"X_API-KEY": str(registered_user_a.api_key)},
    )
    wallet = response.json()["wallet"]
    return Wallet(
        wallet_address=wallet["wallet_address"],
        user_id=registered_user_a.api_key,
        btc_balance=wallet["balance_btc"],
    )


@pytest.fixture
def sender_wallet_b(client: TestClient, registered_user_b: User) -> Wallet:
    response = client.post(
        "/wallets",
        headers={"X_API-KEY": str(registered_user_b.api_key)},
    )
    wallet = response.json()["wallet"]
    return Wallet(
        wallet_address=wallet["wallet_address"],
        user_id=registered_user_b.api_key,
        btc_balance=wallet["balance_btc"],
    )


@pytest.fixture
def recipient_wallet_b(client: TestClient, registered_user_b: User) -> Wallet:
    response = client.post(
        "/wallets",
        headers={"X_API-KEY": str(registered_user_b.api_key)},
    )
    wallet = response.json()["wallet"]
    return Wallet(
        wallet_address=wallet["wallet_address"],
        user_id=registered_user_b.api_key,
        btc_balance=wallet["balance_btc"],
    )


# Test case for successful transaction from the wallet of User A to the wallet of User B
def test_create_transaction_success_different_users(
    client: TestClient,
    registered_user_a: User,
    registered_user_b: User,
    sender_wallet_a: Wallet,
    recipient_wallet_b: Wallet,
) -> None:
    transaction_request = fake_generator.generate_transaction_request(
        sender_wallet_id=sender_wallet_a.wallet_address,
        recipient_wallet_id=recipient_wallet_b.wallet_address,
        amount=0.2,
    )

    response = client.post(
        "/transactions",
        json=transaction_request,
        headers={"X_API-KEY": str(registered_user_a.api_key)},
    )

    sender_wallet_a_after = fetch_wallet_details(
        client, sender_wallet_a.wallet_address, registered_user_a.api_key
    )
    recipient_wallet_b_after = fetch_wallet_details(
        client, recipient_wallet_b.wallet_address, registered_user_b.api_key
    )

    assert response.status_code == 200
    assert "transaction" in response.json()
    created_transaction = response.json()["transaction"]
    validate_transaction_fields(created_transaction)

    assert created_transaction["sender_wallet_id"] == str(
        sender_wallet_a.wallet_address
    )
    assert created_transaction["recipient_wallet_id"] == str(
        recipient_wallet_b.wallet_address
    )
    assert created_transaction["amount_btc"] == 0.2

    assert sender_wallet_a_after["balance_btc"] == sender_wallet_a.btc_balance - 0.2 * (
        1 + created_transaction["fee"]
    )
    assert (
        recipient_wallet_b_after["balance_btc"] == recipient_wallet_b.btc_balance + 0.2
    )


def fetch_wallet_details(
    client: TestClient, wallet_address: UUID, api_key: UUID
) -> Any:
    response = client.get(
        f"/wallets/{wallet_address}",
        headers={"X_API-KEY": str(api_key)},
    )
    assert response.status_code == 200
    assert "wallet" in response.json()
    return response.json()["wallet"]


def validate_transaction_fields(created_transaction: dict[str, Any]) -> None:
    required_fields = [
        "transaction_id",
        "sender_wallet_id",
        "recipient_wallet_id",
        "amount_btc",
        "fee",
        "timestamp",
    ]
    for field in required_fields:
        assert field in created_transaction


# Test case for successful transaction from one wallet to another wallet of User A
def test_create_transaction_success_same_user(
    client: TestClient,
    registered_user_a: User,
    sender_wallet_a: Wallet,
    recipient_wallet_a: Wallet,
) -> None:
    transaction_request = fake_generator.generate_transaction_request(
        sender_wallet_id=sender_wallet_a.wallet_address,
        recipient_wallet_id=recipient_wallet_a.wallet_address,
        amount=0.1,
    )

    response = client.post(
        "/transactions",
        json=transaction_request,
        headers={"X_API-KEY": str(registered_user_a.api_key)},
    )

    sender_wallet_a_after = fetch_wallet_details(
        client, sender_wallet_a.wallet_address, registered_user_a.api_key
    )
    recipient_wallet_a_after = fetch_wallet_details(
        client, recipient_wallet_a.wallet_address, registered_user_a.api_key
    )

    assert response.status_code == 200
    assert "transaction" in response.json()
    created_transaction = response.json()["transaction"]
    validate_transaction_fields(created_transaction)

    assert created_transaction["sender_wallet_id"] == str(
        sender_wallet_a.wallet_address
    )
    assert created_transaction["recipient_wallet_id"] == str(
        recipient_wallet_a.wallet_address
    )
    assert created_transaction["amount_btc"] == 0.1
    assert created_transaction["fee"] == 0

    assert sender_wallet_a_after["balance_btc"] == sender_wallet_a.btc_balance - 0.1 * (
        1 + created_transaction["fee"]
    )
    assert (
        recipient_wallet_a_after["balance_btc"] == recipient_wallet_a.btc_balance + 0.1
    )


# Test case for UserDoesNotExistError
def test_create_transaction_user_not_exist(
    client: TestClient,
    sender_wallet_a: Wallet,
    recipient_wallet_b: Wallet,
) -> None:
    non_existing_user_id = uuid4()  # Assuming this user does not exist
    transaction_request = fake_generator.generate_transaction_request(
        sender_wallet_id=sender_wallet_a.wallet_address,
        recipient_wallet_id=recipient_wallet_b.wallet_address,
        amount=0.2,
    )

    response = client.post(
        "/transactions",
        json=transaction_request,
        headers={"X_API-KEY": str(non_existing_user_id)},
    )
    assert response.status_code == 404
    assert "message" in response.json()
    assert (
        response.json()["message"]
        == f"User with id <{non_existing_user_id}> does not exist"
    )


# Test case for WalletDoesNotExistError
def test_create_sender_wallet_not_exist(
    client: TestClient,
    registered_user_a: User,
    sender_wallet_a: Wallet,
    recipient_wallet_b: Wallet,
) -> None:
    non_existing_wallet_id = uuid4()  # Assuming this wallet does not exist
    transaction_request = fake_generator.generate_transaction_request(
        sender_wallet_id=non_existing_wallet_id,
        recipient_wallet_id=recipient_wallet_b.wallet_address,
        amount=0.2,
    )

    response = client.post(
        "/transactions",
        json=transaction_request,
        headers={"X_API-KEY": str(registered_user_a.api_key)},
    )
    assert response.status_code == 404
    assert "message" in response.json()
    assert response.json()["message"] == "Sender wallet does not exist"


# Test case for WalletDoesNotExistError
def test_create_recipient_wallet_not_exist(
    client: TestClient,
    registered_user_a: User,
    sender_wallet_a: Wallet,
    recipient_wallet_b: Wallet,
) -> None:
    non_existing_wallet_id = uuid4()  # Assuming this wallet does not exist
    transaction_request = fake_generator.generate_transaction_request(
        sender_wallet_id=sender_wallet_a.wallet_address,
        recipient_wallet_id=non_existing_wallet_id,
        amount=0.2,
    )

    response = client.post(
        "/transactions",
        json=transaction_request,
        headers={"X_API-KEY": str(registered_user_a.api_key)},
    )
    assert response.status_code == 404
    assert "message" in response.json()
    assert response.json()["message"] == "Recipient wallet does not exist"


# Test case for WalletOwnershipError
def test_create_transaction_wallet_not_owned(
    client: TestClient,
    registered_user_a: User,
    registered_user_b: User,
    sender_wallet_a: Wallet,
    recipient_wallet_b: Wallet,
) -> None:
    transaction_request = fake_generator.generate_transaction_request(
        sender_wallet_id=sender_wallet_a.wallet_address,
        recipient_wallet_id=recipient_wallet_b.wallet_address,
        amount=0.2,
    )

    response = client.post(
        "/transactions",
        json=transaction_request,
        headers={"X_API-KEY": str(registered_user_b.api_key)},
    )
    assert response.status_code == 403
    assert "message" in response.json()
    assert response.json()["message"] == "Sender wallet does not belong to the user"


# Test case for InsufficientBalanceError
def test_create_transaction_insufficient_balance(
    client: TestClient,
    registered_user_a: User,
    sender_wallet_a: Wallet,
    recipient_wallet_b: Wallet,
) -> None:
    transaction_request = fake_generator.generate_transaction_request(
        sender_wallet_id=sender_wallet_a.wallet_address,
        recipient_wallet_id=recipient_wallet_b.wallet_address,
        amount=sender_wallet_a.btc_balance
        + 1,  # Sending more than the available balance
    )

    response = client.post(
        "/transactions",
        json=transaction_request,
        headers={"X_API-KEY": str(registered_user_a.api_key)},
    )
    assert response.status_code == 409
    assert "message" in response.json()
    assert response.json()["message"] == "Insufficient balance in the sender's wallet"


# Test case for BadRequestError
def test_create_transaction_bad_request(
    client: TestClient,
    registered_user_a: User,
    sender_wallet_a: Wallet,
    recipient_wallet_b: Wallet,
) -> None:
    transaction_request = fake_generator.generate_transaction_request(
        sender_wallet_id=sender_wallet_a.wallet_address,
        recipient_wallet_id=recipient_wallet_b.wallet_address,
        amount=-0.1,
    )
    response = client.post(
        "/transactions",
        json=transaction_request,
        headers={"X_API-KEY": str(registered_user_a.api_key)},
    )
    assert response.status_code == 400
    assert "message" in response.json()
    assert response.json()["message"] == "Negative transaction amount"


def test_get_user_transactions_success(
    client: TestClient,
    registered_user_a: User,
    sender_wallet_a: Wallet,
    recipient_wallet_a: Wallet,
) -> None:
    # Create transactions for the user
    transaction_request_1 = fake_generator.generate_transaction_request(
        sender_wallet_id=sender_wallet_a.wallet_address,
        recipient_wallet_id=recipient_wallet_a.wallet_address,
        amount=0.1,
    )
    transaction_request_2 = fake_generator.generate_transaction_request(
        sender_wallet_id=recipient_wallet_a.wallet_address,
        recipient_wallet_id=sender_wallet_a.wallet_address,
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

    # Retrieve user transactions
    response = client.get(
        "/transactions", headers={"X_API-KEY": str(registered_user_a.api_key)}
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 2  # Two transactions were created
    # Additional assertions as needed


# Test case for UserDoesNotExistError
def test_get_user_transactions_user_not_exist(
    client: TestClient,
    sender_wallet_a: Wallet,
    recipient_wallet_a: Wallet,
) -> None:
    non_existing_user_id = uuid4()  # Assuming this user does not exist

    response = client.get(
        "/transactions", headers={"X_API-KEY": str(non_existing_user_id)}
    )
    assert response.status_code == 404
    assert "message" in response.json()
    assert (
        response.json()["message"]
        == f"User with id <{non_existing_user_id}> does not exist"
    )
