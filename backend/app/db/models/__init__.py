"""SQLAlchemy models registry.

All application database models are registered here so that Base.metadata
contains complete metadata for Alembic migrations and application usage.
"""

from app.db.database import Base
from app.db.models.user import User, UserRole
from app.db.models.department import Department
from app.db.models.employee import Employee, EmployeeStatus
from app.db.models.attendance import Attendance

__all__ = [
    "Base",
    "User",
    "UserRole",
    "Department",
    "Employee",
    "EmployeeStatus",
    "Attendance",
]
