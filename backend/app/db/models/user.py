import enum
from sqlalchemy import BigInteger, CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base, TimestampMixin


class UserRole(str, enum.Enum):
    """Supported application user roles."""
    ADMIN = "ADMIN"
    HR = "HR"


class User(Base, TimestampMixin):
    """User entity for application authentication and authorization."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)

    __table_args__ = (
        CheckConstraint("role IN ('ADMIN', 'HR')", name="ck_users_role"),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r} role={self.role!r}>"
