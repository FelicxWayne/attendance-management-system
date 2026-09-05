from datetime import date, datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CheckInRequest(BaseModel):
    """Schema for marking/checking in employee attendance."""

    employee_id: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Human-facing employee ID (e.g. 'EMP001')",
        examples=["EMP001"],
    )
    attendance_date: Optional[date] = Field(
        default=None,
        description="Attendance date (YYYY-MM-DD). If omitted, defaults to check_in local date in Asia/Kolkata",
        examples=["2026-09-05"],
    )
    check_in: Optional[datetime] = Field(
        default=None,
        description="Timezone-aware timestamp for check-in. If omitted, defaults to current time in Asia/Kolkata",
        examples=["2026-09-05T09:30:00+05:30"],
    )

    @field_validator("employee_id")
    @classmethod
    def validate_employee_id(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("employee_id cannot be empty or whitespace only")
        return stripped

    @field_validator("check_in")
    @classmethod
    def validate_timezone_aware(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value is not None:
            if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
                raise ValueError("check_in must be a timezone-aware timestamp (e.g. 2026-09-05T09:30:00+05:30)")
        return value


class CheckOutRequest(BaseModel):
    """Schema for recording employee check-out."""

    check_out: Optional[datetime] = Field(
        default=None,
        description="Timezone-aware timestamp for check-out. If omitted, defaults to current time in Asia/Kolkata",
        examples=["2026-09-05T18:00:00+05:30"],
    )

    @field_validator("check_out")
    @classmethod
    def validate_timezone_aware(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value is not None:
            if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
                raise ValueError("check_out must be a timezone-aware timestamp (e.g. 2026-09-05T18:00:00+05:30)")
        return value


class AttendanceResponse(BaseModel):
    """Unified attendance response including employee details and computed status."""

    id: Optional[int] = Field(
        default=None,
        description="Attendance record primary key ID (null for computed ABSENT records)",
        examples=[1],
    )
    employee_id: str = Field(
        ...,
        description="Human-facing Employee ID (e.g. 'EMP001')",
        examples=["EMP001"],
    )
    employee_name: str = Field(
        ...,
        description="Full name of the employee",
        examples=["Alice Johnson"],
    )
    department_name: Optional[str] = Field(
        default=None,
        description="Assigned department name",
        examples=["Engineering"],
    )
    attendance_date: date = Field(
        ...,
        description="Date of attendance (YYYY-MM-DD)",
        examples=["2026-09-05"],
    )
    check_in: Optional[datetime] = Field(
        default=None,
        description="Timezone-aware check-in timestamp",
        examples=["2026-09-05T09:30:00+05:30"],
    )
    check_out: Optional[datetime] = Field(
        default=None,
        description="Timezone-aware check-out timestamp",
        examples=["2026-09-05T18:00:00+05:30"],
    )
    status: str = Field(
        default="PRESENT",
        description="Computed status: 'PRESENT' if attendance record exists, 'ABSENT' if employee lacked record",
        examples=["PRESENT"],
    )

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="wrap")
    @classmethod
    def resolve_from_orm(cls, data: Any, handler: Any) -> "AttendanceResponse":
        """Resolve employee and department fields if data is an ORM Attendance model."""
        from zoneinfo import ZoneInfo
        kolkata_tz = ZoneInfo("Asia/Kolkata")

        if hasattr(data, "employee") and data.employee is not None:
            dept_name = None
            if hasattr(data.employee, "department") and data.employee.department is not None:
                dept_name = getattr(data.employee.department, "name", None)

            check_in_val = data.check_in
            if check_in_val is not None and check_in_val.tzinfo is None:
                check_in_val = check_in_val.replace(tzinfo=kolkata_tz)

            check_out_val = data.check_out
            if check_out_val is not None and check_out_val.tzinfo is None:
                check_out_val = check_out_val.replace(tzinfo=kolkata_tz)

            return cls(
                id=data.id,
                employee_id=data.employee.employee_id,
                employee_name=data.employee.name,
                department_name=dept_name,
                attendance_date=data.attendance_date,
                check_in=check_in_val,
                check_out=check_out_val,
                status="PRESENT",
            )
        return handler(data)


class AttendanceListResponse(BaseModel):
    """Paginated collection of attendance records."""

    items: List[AttendanceResponse]
    total: int = Field(..., description="Total count of attendance records matching query criteria")
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Number of items returned per page")
    total_pages: int = Field(..., description="Total number of available pages")

    model_config = ConfigDict(from_attributes=True)


class DailyAttendanceSummaryResponse(BaseModel):
    """Daily attendance summary for active employees with computed PRESENT/ABSENT breakdown."""

    attendance_date: date = Field(..., description="Target date for attendance status")
    total_active_employees: int = Field(..., description="Total number of active employees")
    present_count: int = Field(..., description="Number of active employees present on this date")
    absent_count: int = Field(..., description="Number of active employees absent on this date")
    items: List[AttendanceResponse] = Field(..., description="Paginated employee daily attendance status")
    total: int = Field(..., description="Total count of employees in this status view")
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of available pages")

    model_config = ConfigDict(from_attributes=True)
