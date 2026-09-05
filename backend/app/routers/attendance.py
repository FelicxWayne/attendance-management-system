from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Body, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_role
from app.schemas.attendance import (
    AttendanceListResponse,
    AttendanceResponse,
    CheckInRequest,
    CheckOutRequest,
    DailyAttendanceSummaryResponse,
)
from app.services.attendance_service import attendance_service

# Attendance endpoints require either ADMIN or HR role privileges
router = APIRouter(
    prefix="/attendance",
    tags=["Attendance"],
    dependencies=[Depends(require_role("ADMIN", "HR"))],
)


@router.post(
    "",
    response_model=AttendanceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Check-in employee attendance",
    description="Mark attendance for an active employee. Checks for existing check-in on the same date and enforces timezone-aware timestamps in Asia/Kolkata.",
)
def check_in(
    payload: CheckInRequest,
    db: Session = Depends(get_db),
):
    """Mark attendance check-in for an employee."""
    return attendance_service.check_in(db, payload)


# Route aliases for check-in
@router.post(
    "/check-in",
    response_model=AttendanceResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
@router.post(
    "/checkin",
    response_model=AttendanceResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def check_in_alias(
    payload: CheckInRequest,
    db: Session = Depends(get_db),
):
    """Alias route for employee check-in."""
    return attendance_service.check_in(db, payload)


@router.put(
    "/{attendance_id}/checkout",
    response_model=AttendanceResponse,
    status_code=status.HTTP_200_OK,
    summary="Check-out employee attendance",
    description="Record check-out for an existing attendance record using the attendance primary key ID.",
)
def check_out(
    attendance_id: int,
    payload: Optional[CheckOutRequest] = None,
    db: Session = Depends(get_db),
):
    """Record attendance check-out using attendance record ID."""
    check_out_val = payload.check_out if payload else None
    return attendance_service.check_out_by_id(db, attendance_id, check_out_val)


@router.get(
    "/daily-status",
    response_model=DailyAttendanceSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get daily attendance status and summary",
    description="Retrieve daily summary with computed PRESENT and ABSENT counts and employee list for a given date in Asia/Kolkata.",
)
def get_daily_status(
    attendance_date: Optional[date] = Query(None, description="Date (YYYY-MM-DD), defaults to today in Asia/Kolkata"),
    department_id: Optional[int] = Query(None, description="Filter by department ID"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """Retrieve daily attendance status breakdown for active employees."""
    return attendance_service.get_daily_status(
        db=db,
        attendance_date=attendance_date,
        department_id=department_id,
        page=page,
        page_size=page_size,
    )


@router.get(
    "",
    response_model=AttendanceListResponse,
    status_code=status.HTTP_200_OK,
    summary="List, filter, and paginate attendance records",
    description="Retrieve paginated attendance records with optional filtering by date, date range, employee, and department, with whitelisted deterministic sorting.",
)
def list_attendance(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page (max 100)"),
    attendance_date: Optional[date] = Query(None, description="Exact attendance date (YYYY-MM-DD)"),
    start_date: Optional[date] = Query(None, description="Start date for range filtering (inclusive)"),
    end_date: Optional[date] = Query(None, description="End date for range filtering (inclusive)"),
    employee_id: Optional[str] = Query(None, description="Filter by human-facing employee ID"),
    department_id: Optional[int] = Query(None, description="Filter by department ID"),
    include_absent: bool = Query(
        False,
        description="When attendance_date is set, includes active employees without records computed as ABSENT",
    ),
    sort_by: str = Query(
        "attendance_date",
        description="Sort column: 'attendance_date', 'check_in', 'check_out', 'created_at', 'employee_id'",
    ),
    sort_order: str = Query(
        "desc",
        description="Sort direction: 'asc', 'desc'",
    ),
    db: Session = Depends(get_db),
):
    """List attendance records according to query filters and pagination."""
    return attendance_service.list_attendance(
        db=db,
        page=page,
        page_size=page_size,
        attendance_date=attendance_date,
        start_date=start_date,
        end_date=end_date,
        employee_id=employee_id,
        department_id=department_id,
        include_absent=include_absent,
        sort_by=sort_by,
        sort_order=sort_order,
    )
