from datetime import timedelta
import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.dependencies import get_current_user, get_db, require_role
from app.core.security import create_access_token, hash_password, verify_password
from app.db.database import Base
from app.db.models.user import User, UserRole
from app.main import app

# In-memory SQLite engine dedicated to authentication tests
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Temporary test endpoints to verify require_role RBAC dependency
@app.get("/api/v1/test/admin-only", tags=["Test"])
def admin_only_endpoint(current_user: User = Depends(require_role("ADMIN"))):
    return {"status": "ok", "user": current_user.username}


@app.get("/api/v1/test/admin-or-hr", tags=["Test"])
def admin_or_hr_endpoint(current_user: User = Depends(require_role("ADMIN", "HR"))):
    return {"status": "ok", "user": current_user.username}


@pytest.fixture(autouse=True)
def setup_test_db():
    """Setup and teardown in-memory SQLite tables with seeded test users."""
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()

    admin_user = User(
        id=1,
        username="admin_user",
        password_hash=hash_password("AdminSecret123!"),
        role=UserRole.ADMIN.value,
    )
    hr_user = User(
        id=2,
        username="hr_user",
        password_hash=hash_password("HrSecret123!"),
        role=UserRole.HR.value,
    )
    db.add(admin_user)
    db.add(hr_user)
    db.commit()
    db.close()

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


client = TestClient(app)


def test_password_hashing_and_verification_logic():
    """Verify raw password hashes securely and verification succeeds."""
    raw = "MyP@ssword999!"
    hashed = hash_password(raw)
    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_login_success():
    """Verify valid login returns HTTP 200 with JWT access_token and bearer type."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin_user", "password": "AdminSecret123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "password" not in data
    assert "password_hash" not in data


def test_login_invalid_password():
    """Verify incorrect password returns HTTP 401 with generic error message."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin_user", "password": "WrongPassword123!"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"
    assert "WWW-Authenticate" in response.headers


def test_login_invalid_username():
    """Verify non-existent username returns HTTP 401 with same generic error."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "non_existent_user", "password": "AnyPassword!"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"
    assert "WWW-Authenticate" in response.headers


def test_get_me_success():
    """Verify GET /api/v1/auth/me returns authenticated user details excluding secrets."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"username": "admin_user", "password": "AdminSecret123!"},
    )
    token = login_resp.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["username"] == "admin_user"
    assert user_data["role"] == "ADMIN"
    assert "id" in user_data
    assert "created_at" in user_data
    assert "password" not in user_data
    assert "password_hash" not in user_data


def test_get_me_missing_token():
    """Verify GET /api/v1/auth/me rejects requests without token with HTTP 401."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.headers.get("WWW-Authenticate") == "Bearer"


def test_get_me_invalid_token():
    """Verify GET /api/v1/auth/me rejects requests with malformed tokens with HTTP 401."""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.token.value"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_get_me_expired_token():
    """Verify GET /api/v1/auth/me rejects expired tokens with HTTP 401."""
    # Create token already expired 5 minutes ago
    expired_token = create_access_token(
        data={"sub": "1", "role": "ADMIN"},
        expires_delta=timedelta(minutes=-5),
    )
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Token has expired"


def test_get_me_user_no_longer_exists():
    """Verify valid token referencing deleted user ID returns HTTP 401."""
    token = create_access_token(data={"sub": "99999", "role": "ADMIN"})
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "User not found"


def test_rbac_admin_role_enforcement():
    """Verify RBAC restricts access based on role (ADMIN allowed, HR forbidden with 403)."""
    # 1. Login as ADMIN
    admin_login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin_user", "password": "AdminSecret123!"},
    )
    admin_token = admin_login.json()["access_token"]

    # 2. Login as HR
    hr_login = client.post(
        "/api/v1/auth/login",
        json={"username": "hr_user", "password": "HrSecret123!"},
    )
    hr_token = hr_login.json()["access_token"]

    # ADMIN accessing admin-only endpoint -> 200 OK
    admin_resp = client.get(
        "/api/v1/test/admin-only",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_resp.status_code == 200
    assert admin_resp.json()["user"] == "admin_user"

    # HR accessing admin-only endpoint -> 403 Forbidden
    hr_resp = client.get(
        "/api/v1/test/admin-only",
        headers={"Authorization": f"Bearer {hr_token}"},
    )
    assert hr_resp.status_code == 403
    assert hr_resp.json()["detail"] == "Operation not permitted for current role"

    # Both accessing multi-role endpoint -> 200 OK
    resp1 = client.get(
        "/api/v1/test/admin-or-hr",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    resp2 = client.get(
        "/api/v1/test/admin-or-hr",
        headers={"Authorization": f"Bearer {hr_token}"},
    )
    assert resp1.status_code == 200
    assert resp2.status_code == 200


def test_swagger_openapi_uses_http_bearer():
    """Verify Swagger/OpenAPI schema configures HTTPBearer and excludes OAuth2PasswordBearer."""
    openapi_schema = app.openapi()
    security_schemes = openapi_schema.get("components", {}).get("securitySchemes", {})

    # Ensure HTTPBearer security scheme exists and is correctly configured
    assert "HTTPBearer" in security_schemes
    assert security_schemes["HTTPBearer"]["type"] == "http"
    assert security_schemes["HTTPBearer"]["scheme"] == "bearer"

    # Ensure OAuth2 password flow is NOT used (which caused the Swagger 422 error)
    assert "OAuth2PasswordBearer" not in security_schemes

    # Ensure /api/v1/auth/me references HTTPBearer security
    me_operation = openapi_schema["paths"]["/api/v1/auth/me"]["get"]
    assert "security" in me_operation
    assert {"HTTPBearer": []} in me_operation["security"]


def test_get_me_non_bearer_auth_header():
    """Verify GET /api/v1/auth/me rejects non-Bearer authorization schemes with HTTP 401."""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Basic dXNlcjpwYXNz"},
    )
    assert response.status_code == 401
    assert response.headers.get("WWW-Authenticate") == "Bearer"
    assert response.json()["detail"] == "Authentication credentials were not provided"

