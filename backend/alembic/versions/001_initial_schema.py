"""Initial database schema: users, departments, employees, attendance

Revision ID: 001_initial_schema
Revises: None
Create Date: 2026-09-05 00:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. USERS TABLE
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("username", name="uq_users_username"),
        sa.CheckConstraint("role IN ('ADMIN', 'HR')", name="ck_users_role"),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    # 2. DEPARTMENTS TABLE
    op.create_table(
        "departments",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_departments"),
        sa.UniqueConstraint("name", name="uq_departments_name"),
    )
    op.create_index("ix_departments_name", "departments", ["name"], unique=True)

    # 3. EMPLOYEES TABLE
    op.create_table(
        "employees",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("employee_code", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("mobile", sa.String(length=20), nullable=True),
        sa.Column("department_id", sa.BigInteger(), nullable=False),
        sa.Column("designation", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="ACTIVE", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_employees"),
        sa.UniqueConstraint("employee_code", name="uq_employees_employee_code"),
        sa.ForeignKeyConstraint(
            ["department_id"],
            ["departments.id"],
            name="fk_employees_department_id",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint("status IN ('ACTIVE', 'INACTIVE')", name="ck_employees_status"),
    )
    op.create_index("ix_employees_department_id", "employees", ["department_id"], unique=False)
    # Functional unique index on lower(email)
    op.create_index(
        "ix_employees_lower_email",
        "employees",
        [sa.text("lower(email)")],
        unique=True,
    )

    # 4. ATTENDANCE TABLE
    op.create_table(
        "attendance",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("employee_id", sa.BigInteger(), nullable=False),
        sa.Column("attendance_date", sa.Date(), nullable=False),
        sa.Column("check_in", sa.DateTime(timezone=True), nullable=False),
        sa.Column("check_out", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_attendance"),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["employees.id"],
            name="fk_attendance_employee_id",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("employee_id", "attendance_date", name="uq_attendance_employee_date"),
        sa.CheckConstraint(
            "check_out IS NULL OR check_out > check_in",
            name="ck_attendance_checkout_after_checkin",
        ),
    )
    op.create_index("ix_attendance_attendance_date", "attendance", ["attendance_date"], unique=False)


def downgrade() -> None:
    # Drop in strict reverse dependency order: attendance -> employees -> departments -> users

    # 1. Drop attendance table and indexes
    op.drop_index("ix_attendance_attendance_date", table_name="attendance")
    op.drop_table("attendance")

    # 2. Drop employees table and indexes
    op.drop_index("ix_employees_lower_email", table_name="employees")
    op.drop_index("ix_employees_department_id", table_name="employees")
    op.drop_table("employees")

    # 3. Drop departments table and indexes
    op.drop_index("ix_departments_name", table_name="departments")
    op.drop_table("departments")

    # 4. Drop users table and indexes
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
