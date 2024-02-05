import pytest
from fastapi.testclient import TestClient

from runner.setup import init_test_app
from tests.fake import FakeGenerator


@pytest.fixture
def client() -> TestClient:
    return TestClient(init_test_app())


fake = FakeGenerator()


def test_register_user_success(client: TestClient) -> None:
    registration_request = fake.generate_registration_request()

    # Test user registration
    response = client.post("/users", json=registration_request)
    assert response.status_code == 201
    assert "api_key" in response.json()


def test_register_existing_user(client: TestClient) -> None:
    registration_request = fake.generate_registration_request()

    # Test user registration
    response = client.post("/users", json=registration_request)
    assert response.status_code == 201

    # Test registering an existing user (should return 409 Conflict)
    response = client.post("/users", json=registration_request)
    assert response.status_code == 409
    email = registration_request["email"]
    assert f"User with email <{email}> already exists" in response.text


def test_register_user_invalid_email(client: TestClient) -> None:
    registration_request = {"email": "invalid_email", "password": "password"}

    # Test user registration with invalid email (should return 400 Bad Request)
    response = client.post("/users", json=registration_request)
    assert response.status_code == 400
    assert "Invalid email address" in response.text
