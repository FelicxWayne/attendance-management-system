"""Rename employee_code column to employee_id in employees table

Revision ID: 002_rename_employee_id
Revises: 001_initial_schema
Create Date: 2026-09-05 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "002_rename_employee_id"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename column and update unique constraint to preserve uniqueness on employee_id
    with op.batch_alter_table("employees") as batch_op:
        batch_op.alter_column(
            "employee_code",
            new_column_name="employee_id",
            existing_type=sa.String(length=20),
            existing_nullable=False,
        )
        batch_op.drop_constraint("uq_employees_employee_code", type_="unique")
        batch_op.create_unique_constraint("uq_employees_employee_id", ["employee_id"])


def downgrade() -> None:
    with op.batch_alter_table("employees") as batch_op:
        batch_op.alter_column(
            "employee_id",
            new_column_name="employee_code",
            existing_type=sa.String(length=20),
            existing_nullable=False,
        )
        batch_op.drop_constraint("uq_employees_employee_id", type_="unique")
        batch_op.create_unique_constraint("uq_employees_employee_code", ["employee_code"])
