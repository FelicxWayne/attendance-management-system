from typing import TYPE_CHECKING, List
from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.employee import Employee


class Department(Base, TimestampMixin):
    """Department entity representing organizational divisions."""

    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)

    # 1-to-many relationship: One department has many employees
    employees: Mapped[List["Employee"]] = relationship(
        "Employee",
        back_populates="department",
        passive_deletes="all",
    )

    def __repr__(self) -> str:
        return f"<Department id={self.id} name={self.name!r}>"
