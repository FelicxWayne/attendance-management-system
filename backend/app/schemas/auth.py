from datetime import datetime
from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    """Schema for user credentials submitted during authentication."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """Schema for successful authentication access token payload."""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Safe schema for returning user profile details (excludes password hashes)."""

    id: int
    username: str
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
