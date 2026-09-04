from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    APP_NAME: str = "Attendance Management System"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@db:5432/attendance_db"

    JWT_SECRET_KEY: str = "change-me-default-secret-key-minimum-32-chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Return CORS origins as a parsed list of strings."""
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        if isinstance(self.CORS_ORIGINS, str):
            # Supports both comma-separated strings and single origins
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        return []


settings = Settings()
