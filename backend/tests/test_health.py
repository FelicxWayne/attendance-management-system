from fastapi.testclient import TestClient

from app.main import app
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)

client = TestClient(app)


def test_health_check():
    """Verify GET /health returns HTTP 200 and {'status': 'ok'}."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_endpoint():
    """Verify GET / returns HTTP 200 with service welcome info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["health"] == "/health"
    assert data["docs"] == "/docs"


def test_password_hashing_and_verification():
    """Verify bcrypt hashing and verification utility functions."""
    raw_password = "SecurePassword123!"
    hashed = hash_password(raw_password)

    assert hashed != raw_password
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_jwt_creation_and_decoding():
    """Verify JWT token creation with subject and role claims."""
    payload = {"sub": "user-uuid-1234", "role": "admin"}
    token = create_access_token(data=payload)

    decoded = decode_access_token(token)
    assert decoded["sub"] == "user-uuid-1234"
    assert decoded["role"] == "admin"
    assert "exp" in decoded
