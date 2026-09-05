from datetime import datetime
import re
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.db.models.employee import EmployeeStatus

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class DepartmentSummary(BaseModel):
    """Minimal department information included with employee responses."""

    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class EmployeeCreate(BaseModel):
    """Schema for creating a new employee."""

    employee_id: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Unique identifier for the employee (max 20 chars)",
        examples=["EMP001"],
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Full name of the employee (max 100 chars)",
        examples=["Jane Doe"],
    )
    email: str = Field(
        ...,
        max_length=255,
        description="Corporate email address (unique case-insensitively)",
        examples=["jane.doe@company.com"],
    )
    mobile: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Optional contact telephone/mobile number",
        examples=["+1-555-0199"],
    )
    department_id: int = Field(
        ...,
        gt=0,
        description="ID of the assigned department (must reference existing department)",
        examples=[1],
    )
    designation: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Job title or role designation",
        examples=["Software Engineer"],
    )

    @field_validator("employee_id", "name", "designation")
    @classmethod
    def strip_and_validate_non_empty(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field cannot be empty or whitespace only")
        return stripped

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped or not EMAIL_REGEX.match(stripped):
            raise ValueError("Invalid email format")
        return stripped

    @field_validator("mobile")
    @classmethod
    def strip_optional_mobile(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip()
        return stripped if stripped else None


class EmployeeUpdate(BaseModel):
    """Schema for updating an existing employee's details."""

    employee_id: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Unique identifier for the employee",
        examples=["EMP001"],
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Full name of the employee",
        examples=["Jane Doe"],
    )
    email: str = Field(
        ...,
        max_length=255,
        description="Corporate email address",
        examples=["jane.doe@company.com"],
    )
    mobile: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Optional contact telephone/mobile number",
        examples=["+1-555-0199"],
    )
    department_id: int = Field(
        ...,
        gt=0,
        description="ID of the assigned department",
        examples=[1],
    )
    designation: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Job title or role designation",
        examples=["Senior Software Engineer"],
    )
    status: EmployeeStatus = Field(
        ...,
        description="Employee lifecycle status: ACTIVE or INACTIVE",
        examples=[EmployeeStatus.ACTIVE],
    )

    @field_validator("employee_id", "name", "designation")
    @classmethod
    def strip_and_validate_non_empty(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field cannot be empty or whitespace only")
        return stripped

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped or not EMAIL_REGEX.match(stripped):
            raise ValueError("Invalid email format")
        return stripped

    @field_validator("mobile")
    @classmethod
    def strip_optional_mobile(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip()
        return stripped if stripped else None


class EmployeeResponse(BaseModel):
    """Schema for returning employee details."""

    id: int
    employee_id: str
    name: str
    email: str
    mobile: Optional[str] = None
    department_id: int
    department_name: Optional[str] = None
    department: Optional[DepartmentSummary] = None
    designation: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="wrap")
    @classmethod
    def resolve_department_name(cls, data, handler):
        res = handler(data)
        if hasattr(data, "department") and data.department is not None:
            res.department_name = getattr(data.department, "name", None)
        elif res.department and res.department.name:
            res.department_name = res.department.name
        return res


class EmployeeListResponse(BaseModel):
    """Paginated collection of employee records."""

    items: List[EmployeeResponse]
    total: int = Field(..., description="Total count of employees matching query criteria")
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Number of items returned per page")
    total_pages: int = Field(..., description="Total number of available pages")

    model_config = ConfigDict(from_attributes=True)
