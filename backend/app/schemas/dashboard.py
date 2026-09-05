from typing import List
from pydantic import BaseModel, ConfigDict, Field


class DepartmentEmployeeCount(BaseModel):
    """Department-wise employee count breakdown."""

    department_id: int = Field(..., description="Unique department identifier", examples=[1])
    department_name: str = Field(..., description="Department name", examples=["Engineering"])
    employee_count: int = Field(
        ...,
        ge=0,
        description="Total employee count belonging to the department (active + inactive)",
        examples=[5],
    )

    model_config = ConfigDict(from_attributes=True)


class DashboardResponse(BaseModel):
    """Consolidated operational dashboard metrics response."""

    total_employees: int = Field(
        ...,
        ge=0,
        description="Total count of all employees in the system (active and inactive)",
        examples=[10],
    )
    active_employees: int = Field(
        ...,
        ge=0,
        description="Count of currently active employees",
        examples=[8],
    )
    present_today: int = Field(
        ...,
        ge=0,
        description="Count of active employees who have an attendance record for today",
        examples=[6],
    )
    absent_today: int = Field(
        ...,
        ge=0,
        description="Count of active employees who do not have an attendance record for today",
        examples=[2],
    )
    department_counts: List[DepartmentEmployeeCount] = Field(
        default_factory=list,
        description="Employee distribution count across all departments",
    )

    model_config = ConfigDict(from_attributes=True)
