from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from core.users.repository import User
from runner.setup import init_test_app
from tests.fake import FakeGenerator


@pytest.fixture
def client() -> TestClient:
    return TestClient(init_test_app())


fake_generator = FakeGenerator()


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


def test_create_wallet(client: TestClient, registered_user_a: User) -> None:
    response = client.post(
        "/wallets",
        headers=fake_generator.generate_wallet_creation_request(
            registered_user_a.api_key
        ),
    )
    assert response.status_code == 201
    assert "wallet" in response.json()
    wallet_data = response.json()["wallet"]
    assert "wallet_address" in wallet_data
    assert "balance_btc" in wallet_data
    assert "balance_usd" in wallet_data
    # Check if the initial balance is 1 BTC
    assert wallet_data["balance_btc"] == 1.0


def test_create_different_wallet_address(
    client: TestClient, registered_user_a: User
) -> None:
    first_response = client.post(
        "/wallets",
        headers=fake_generator.generate_wallet_creation_request(
            registered_user_a.api_key
        ),
    )
    second_response = client.post(
        "/wallets",
        headers=fake_generator.generate_wallet_creation_request(
            registered_user_a.api_key
        ),
    )
    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert (
        first_response.json()["wallet"]["wallet_address"]
        != second_response.json()["wallet"]["wallet_address"]
    )


def test_create_max_wallets_limit(client: TestClient, registered_user_a: User) -> None:
    # Creating 3 wallets for the user
    for _ in range(3):
        response = client.post(
            "/wallets",
            headers=fake_generator.generate_wallet_creation_request(
                registered_user_a.api_key
            ),
        )
        assert response.status_code == 201

    # Attempting to create one more wallet should result in a conflict
    conflict_response = client.post(
        "/wallets",
        headers=fake_generator.generate_wallet_creation_request(
            registered_user_a.api_key
        ),
    )
    assert conflict_response.status_code == 409
    assert "Maximum number of wallets reached for this user" in conflict_response.text


def test_fetch_wallet(client: TestClient, registered_user_a: User) -> None:
    creation_response = client.post(
        "/wallets",
        headers=fake_generator.generate_wallet_creation_request(
            registered_user_a.api_key
        ),
    )
    wallet_data = creation_response.json()["wallet"]
    wallet_address = wallet_data["wallet_address"]
    balance_btc = wallet_data["balance_btc"]
    balance_usd = wallet_data["balance_usd"]

    fetch_response = client.get(
        f"/wallets/{wallet_address}",
        headers=fake_generator.generate_wallet_creation_request(
            registered_user_a.api_key
        ),
    )
    assert fetch_response.status_code == 200
    assert "wallet" in fetch_response.json()
    fetched_wallet_data = fetch_response.json()["wallet"]
    assert fetched_wallet_data["wallet_address"] == wallet_address
    assert fetched_wallet_data["balance_btc"] == balance_btc
    assert fetched_wallet_data["balance_usd"] == balance_usd


def test_fetch_non_existent_wallet(client: TestClient, registered_user_a: User) -> None:
    non_existent_wallet_address = str(uuid4())
    fetch_response = client.get(
        f"/wallets/{non_existent_wallet_address}",
        headers=fake_generator.generate_wallet_creation_request(
            registered_user_a.api_key
        ),
    )
    assert fetch_response.status_code == 404


def test_create_wallet_invalid_api_key(client: TestClient) -> None:
    invalid_api_key = uuid4()
    response = client.post(
        "/wallets",
        headers=fake_generator.generate_wallet_creation_request(invalid_api_key),
    )
    assert response.status_code == 404


def test_fetch_wallet_invalid_api_key(client: TestClient) -> None:
    invalid_api_key = uuid4()
    wallet_address = uuid4()
    response = client.get(
        f"/wallets/{wallet_address}",
        headers=fake_generator.generate_wallet_creation_request(invalid_api_key),
    )
    assert response.status_code == 404


def test_fetch_wallet_not_owner(client: TestClient, registered_user_a: User) -> None:
    # Creating a wallet for another user
    registration_request = fake_generator.generate_registration_request()
    response = client.post("/users", json=registration_request)
    another_api_key = response.json()["api_key"]
    wallet_response = client.post(
        "/wallets",
        headers=fake_generator.generate_wallet_creation_request(another_api_key),
    )
    wallet_address = wallet_response.json()["wallet"]["wallet_address"]

    forbidden_response = client.get(
        f"/wallets/{wallet_address}",
        headers=fake_generator.generate_wallet_creation_request(
            registered_user_a.api_key
        ),
    )
    assert forbidden_response.status_code == 403
