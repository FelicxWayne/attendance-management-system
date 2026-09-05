"""Pydantic request and response schemas."""

from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.schemas.employee import (
    DepartmentSummary,
    EmployeeCreate,
    EmployeeListResponse,
    EmployeeResponse,
    EmployeeUpdate,
)
from app.schemas.attendance import (
    AttendanceListResponse,
    AttendanceResponse,
    CheckInRequest,
    CheckOutRequest,
    DailyAttendanceSummaryResponse,
)
from app.schemas.dashboard import (
    DashboardResponse,
    DepartmentEmployeeCount,
)

__all__ = [
    "LoginRequest",
    "TokenResponse",
    "UserResponse",
    "DepartmentSummary",
    "EmployeeCreate",
    "EmployeeUpdate",
    "EmployeeResponse",
    "EmployeeListResponse",
    "CheckInRequest",
    "CheckOutRequest",
    "AttendanceResponse",
    "AttendanceListResponse",
    "DailyAttendanceSummaryResponse",
    "DepartmentEmployeeCount",
    "DashboardResponse",
]

