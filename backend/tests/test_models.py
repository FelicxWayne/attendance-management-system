from datetime import date, datetime, timezone
import pytest
from sqlalchemy import BigInteger, CheckConstraint, Date, DateTime, ForeignKeyConstraint, Index, String, UniqueConstraint

from app.db.database import Base
from app.db.models import (
    Attendance,
    Department,
    Employee,
    EmployeeStatus,
    User,
    UserRole,
)


def test_tables_registered_in_metadata():
    """Verify that exactly the 4 expected application tables are in metadata."""
    table_names = set(Base.metadata.tables.keys())
    assert table_names == {"users", "departments", "employees", "attendance"}


def test_user_model_schema():
    """Verify User model columns, types, primary key, and check constraint."""
    table = Base.metadata.tables["users"]

    # Primary key
    assert table.c.id.primary_key is True
    assert isinstance(table.c.id.type, BigInteger)

    # Columns and nullability
    assert isinstance(table.c.username.type, String)
    assert table.c.username.type.length == 50
    assert table.c.username.nullable is False
    assert table.c.username.unique is True

    assert isinstance(table.c.password_hash.type, String)
    assert table.c.password_hash.type.length == 255
    assert table.c.password_hash.nullable is False

    assert isinstance(table.c.role.type, String)
    assert table.c.role.type.length == 20
    assert table.c.role.nullable is False

    assert isinstance(table.c.created_at.type, DateTime)
    assert table.c.created_at.type.timezone is True
    assert table.c.created_at.nullable is False

    assert isinstance(table.c.updated_at.type, DateTime)
    assert table.c.updated_at.type.timezone is True
    assert table.c.updated_at.nullable is False

    # Check constraint
    check_constraints = [c for c in table.constraints if isinstance(c, CheckConstraint)]
    role_ck = next((c for c in check_constraints if c.name == "ck_users_role"), None)
    assert role_ck is not None
    assert "role IN ('ADMIN', 'HR')" in str(role_ck.sqltext)


def test_department_model_schema():
    """Verify Department model columns, types, and primary key."""
    table = Base.metadata.tables["departments"]

    assert table.c.id.primary_key is True
    assert isinstance(table.c.id.type, BigInteger)

    assert isinstance(table.c.name.type, String)
    assert table.c.name.type.length == 100
    assert table.c.name.nullable is False
    assert table.c.name.unique is True

    assert isinstance(table.c.created_at.type, DateTime)
    assert table.c.created_at.type.timezone is True
    assert isinstance(table.c.updated_at.type, DateTime)
    assert table.c.updated_at.type.timezone is True


def test_employee_model_schema():
    """Verify Employee model columns, constraints, foreign key, and functional index."""
    table = Base.metadata.tables["employees"]

    assert table.c.id.primary_key is True
    assert isinstance(table.c.id.type, BigInteger)

    assert table.c.employee_code.nullable is False
    assert table.c.employee_code.type.length == 20

    # Single unique constraint uq_employees_employee_code
    unique_constraints = [c for c in table.constraints if isinstance(c, UniqueConstraint)]
    emp_code_uq = next((u for u in unique_constraints if u.name == "uq_employees_employee_code"), None)
    assert emp_code_uq is not None
    assert [col.name for col in emp_code_uq.columns] == ["employee_code"]

    assert table.c.name.nullable is False
    assert table.c.name.type.length == 100

    assert table.c.email.nullable is False
    assert table.c.email.type.length == 255

    assert table.c.mobile.nullable is True
    assert table.c.mobile.type.length == 20

    assert table.c.designation.nullable is False
    assert table.c.designation.type.length == 100

    assert table.c.status.nullable is False
    assert table.c.status.type.length == 20
    assert table.c.status.server_default.arg == "ACTIVE"

    # Department foreign key with ON DELETE RESTRICT
    fk_constraints = [c for c in table.constraints if isinstance(c, ForeignKeyConstraint)]
    dept_fk = next((fk for fk in fk_constraints if "department_id" in [col.name for col in fk.columns]), None)
    assert dept_fk is not None
    assert dept_fk.ondelete == "RESTRICT"
    assert [elem.target_fullname for elem in dept_fk.elements] == ["departments.id"]

    # Status check constraint
    check_constraints = [c for c in table.constraints if isinstance(c, CheckConstraint)]
    status_ck = next((c for c in check_constraints if c.name == "ck_employees_status"), None)
    assert status_ck is not None
    assert "status IN ('ACTIVE', 'INACTIVE')" in str(status_ck.sqltext)

    # Functional index on lower(email)
    indexes = list(table.indexes)
    lower_email_idx = next((idx for idx in indexes if idx.name == "ix_employees_lower_email"), None)
    assert lower_email_idx is not None
    assert lower_email_idx.unique is True

    # Redundant index ix_employees_employee_code must NOT exist
    emp_code_idx = next((idx for idx in indexes if idx.name == "ix_employees_employee_code"), None)
    assert emp_code_idx is None


def test_attendance_model_schema():
    """Verify Attendance model has NO status column, and verifies all constraints and indexes."""
    table = Base.metadata.tables["attendance"]

    # CRITICAL: Confirm attendance table does NOT store a status column
    assert "status" not in table.c

    assert table.c.id.primary_key is True
    assert isinstance(table.c.id.type, BigInteger)

    assert isinstance(table.c.attendance_date.type, Date)
    assert table.c.attendance_date.nullable is False

    assert isinstance(table.c.check_in.type, DateTime)
    assert table.c.check_in.type.timezone is True
    assert table.c.check_in.nullable is False

    assert isinstance(table.c.check_out.type, DateTime)
    assert table.c.check_out.type.timezone is True
    assert table.c.check_out.nullable is True

    # Employee foreign key with ON DELETE RESTRICT
    fk_constraints = [c for c in table.constraints if isinstance(c, ForeignKeyConstraint)]
    emp_fk = next((fk for fk in fk_constraints if "employee_id" in [col.name for col in fk.columns]), None)
    assert emp_fk is not None
    assert emp_fk.ondelete == "RESTRICT"
    assert [elem.target_fullname for elem in emp_fk.elements] == ["employees.id"]

    # Unique constraint on (employee_id, attendance_date)
    unique_constraints = [c for c in table.constraints if isinstance(c, UniqueConstraint)]
    emp_date_uq = next((u for u in unique_constraints if u.name == "uq_attendance_employee_date"), None)
    assert emp_date_uq is not None
    assert {col.name for col in emp_date_uq.columns} == {"employee_id", "attendance_date"}

    # Check constraint: check_out IS NULL OR check_out > check_in
    check_constraints = [c for c in table.constraints if isinstance(c, CheckConstraint)]
    checkout_ck = next((c for c in check_constraints if c.name == "ck_attendance_checkout_after_checkin"), None)
    assert checkout_ck is not None
    assert "check_out IS NULL OR check_out > check_in" in str(checkout_ck.sqltext)

    # Index on attendance_date
    indexes = list(table.indexes)
    date_idx = next((idx for idx in indexes if idx.name == "ix_attendance_attendance_date"), None)
    assert date_idx is not None

    # Separate employee_id index is intentionally not present because
    # the composite unique constraint uq_attendance_employee_date covers employee_id prefix lookups
    emp_idx = next((idx for idx in indexes if idx.name == "ix_attendance_employee_id"), None)
    assert emp_idx is None


def test_orm_relationships():
    """Verify ORM bidirectional relationships among Department, Employee, and Attendance."""
    # Department <-> Employee
    assert hasattr(Department, "employees")
    assert Department.employees.property.mapper.class_ is Employee
    assert hasattr(Employee, "department")
    assert Employee.department.property.mapper.class_ is Department

    # Employee <-> Attendance
    assert hasattr(Employee, "attendances")
    assert Employee.attendances.property.mapper.class_ is Attendance
    assert hasattr(Attendance, "employee")
    assert Attendance.employee.property.mapper.class_ is Employee


def test_model_instantiation():
    """Verify models can be cleanly instantiated in Python."""
    user = User(username="admin_user", password_hash="hashed_secret", role=UserRole.ADMIN.value)
    assert user.username == "admin_user"
    assert user.role == "ADMIN"

    dept = Department(name="Engineering")
    assert dept.name == "Engineering"

    emp = Employee(
        employee_code="EMP001",
        name="Alex Smith",
        email="alex.smith@example.com",
        designation="Software Engineer",
        status=EmployeeStatus.ACTIVE.value,
        department=dept,
    )
    assert emp.employee_code == "EMP001"
    assert emp.department.name == "Engineering"

    att = Attendance(
        employee=emp,
        attendance_date=date(2026, 9, 5),
        check_in=datetime(2026, 9, 5, 9, 0, 0, tzinfo=timezone.utc),
    )
    assert att.employee.employee_code == "EMP001"
    assert att.attendance_date == date(2026, 9, 5)
    assert att.check_out is None
