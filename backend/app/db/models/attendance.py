from datetime import date, datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.employee import Employee


class Attendance(Base, TimestampMixin):
    """Attendance entity recording actual employee presence.

    Architectural Note:
    Attendance status ('PRESENT' / 'ABSENT') is NOT stored as a database column.
    The presence of an attendance record for an employee on a given date indicates 'PRESENT'.
    Absence is computed dynamically at the query/service layer for ACTIVE employees lacking a record.
    """

    __tablename__ = "attendance"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("employees.id", ondelete="RESTRICT"),
        nullable=False,
    )
    attendance_date: Mapped[date] = mapped_column(Date, nullable=False)
    check_in: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    check_out: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    employee: Mapped["Employee"] = relationship(
        "Employee",
        back_populates="attendances",
    )

    __table_args__ = (
        # Prevent duplicate attendance records for the same employee on the same date
        UniqueConstraint("employee_id", "attendance_date", name="uq_attendance_employee_date"),
        # Ensure checkout occurs strictly after check-in when provided
        CheckConstraint(
            "check_out IS NULL OR check_out > check_in",
            name="ck_attendance_checkout_after_checkin",
        ),
        # Optimize daily dashboard and attendance queries
        Index("ix_attendance_attendance_date", "attendance_date"),
    )

    def __repr__(self) -> str:
        return (
            f"<Attendance id={self.id} employee_id={self.employee_id} "
            f"date={self.attendance_date} check_in={self.check_in} check_out={self.check_out}>"
        )
