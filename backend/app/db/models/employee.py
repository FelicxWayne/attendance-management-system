import enum
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.department import Department
    from app.db.models.attendance import Attendance


class EmployeeStatus(str, enum.Enum):
    """Allowed employee lifecycle statuses."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Employee(Base, TimestampMixin):
    """Employee entity capturing staff details and department assignment."""

    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    employee_code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    mobile: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    department_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("departments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    designation: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=EmployeeStatus.ACTIVE.value,
    )

    # Relationships
    department: Mapped["Department"] = relationship(
        "Department",
        back_populates="employees",
    )
    attendances: Mapped[List["Attendance"]] = relationship(
        "Attendance",
        back_populates="employee",
        passive_deletes="all",
    )

    __table_args__ = (
        UniqueConstraint("employee_code", name="uq_employees_employee_code"),
        CheckConstraint("status IN ('ACTIVE', 'INACTIVE')", name="ck_employees_status"),
        Index("ix_employees_lower_email", text("lower(email)"), unique=True),
    )

    def __repr__(self) -> str:
        return f"<Employee id={self.id} code={self.employee_code!r} name={self.name!r} status={self.status!r}>"
