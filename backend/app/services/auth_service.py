from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.db.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse


class AuthService:
    """Service handling credential verification and JWT access token issuance."""

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """Verify user credentials against the database.

        Returns User entity on match; returns None on incorrect username or password.
        """
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    @classmethod
    def login(cls, db: Session, login_data: LoginRequest) -> TokenResponse:
        """Authenticate user and issue a signed JWT access token.

        Raises HTTP 401 Unauthorized with generic error on failure.
        """
        user = cls.authenticate_user(db, login_data.username, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # JWT payload carries user identity and role claims
        token_payload = {
            "sub": str(user.id),
            "role": user.role,
        }
        access_token = create_access_token(data=token_payload)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
        )


auth_service = AuthService()
