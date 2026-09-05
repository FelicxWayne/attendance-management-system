from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_role
from app.db.models.employee import EmployeeStatus
from app.schemas.attendance import AttendanceListResponse
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeListResponse,
    EmployeeResponse,
    EmployeeUpdate,
)
from app.services.attendance_service import attendance_service
from app.services.employee_service import employee_service

# All employee endpoints require either ADMIN or HR role privileges
router = APIRouter(
    prefix="/employees",
    tags=["Employees"],
    dependencies=[Depends(require_role("ADMIN", "HR"))],
)


@router.post(
    "",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new employee",
    description="Register a new employee with default ACTIVE status. Enforces unique employee_id and unique email.",
)
def create_employee(
    employee_in: EmployeeCreate,
    db: Session = Depends(get_db),
):
    """Create and persist a new employee entity."""
    return employee_service.create_employee(db, employee_in)


@router.get(
    "",
    response_model=EmployeeListResponse,
    status_code=status.HTTP_200_OK,
    summary="List, search, filter, and paginate employees",
    description="Retrieve a paginated list of employees with optional search across employee_id/name/email, status filtering, department filtering, and safe whitelisted sorting.",
)
def list_employees(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page (maximum 100)"),
    search: Optional[str] = Query(None, description="Case-insensitive search across employee_id, name, and email"),
    status: Optional[EmployeeStatus] = Query(None, description="Filter by status: ACTIVE or INACTIVE"),
    department_id: Optional[int] = Query(None, description="Filter by department ID"),
    sort_by: str = Query(
        "created_at",
        description="Field to sort by (allowed: 'employee_id', 'name', 'created_at')",
    ),
    sort_order: str = Query(
        "desc",
        description="Sort direction (allowed: 'asc', 'desc')",
    ),
    db: Session = Depends(get_db),
):
    """List employees matching filtering and pagination parameters."""
    return employee_service.list_employees(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        status_filter=status,
        department_id=department_id,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get(
    "/{employee_id}",
    response_model=EmployeeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get employee details",
    description="Retrieve detailed profile information for an employee by primary key.",
)
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
):
    """Fetch employee by ID."""
    return employee_service.get_employee_by_id(db, employee_id)


@router.put(
    "/{employee_id}",
    response_model=EmployeeResponse,
    status_code=status.HTTP_200_OK,
    summary="Edit an employee",
    description="Update employee details. Validates uniqueness against other employees and ensures department existence.",
)
def update_employee(
    employee_id: int,
    employee_in: EmployeeUpdate,
    db: Session = Depends(get_db),
):
    """Update employee by ID."""
    return employee_service.update_employee(db, employee_id, employee_in)


@router.delete(
    "/{employee_id}",
    response_model=EmployeeResponse,
    status_code=status.HTTP_200_OK,
    summary="Deactivate an employee",
    description="Logically deactivates an employee by setting status to INACTIVE. Preserves database records and relationships.",
)
def deactivate_employee(
    employee_id: int,
    db: Session = Depends(get_db),
):
    """Logically deactivate employee by setting status to INACTIVE."""
    return employee_service.deactivate_employee(db, employee_id)


@router.get(
    "/{employee_id}/attendance",
    response_model=AttendanceListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get employee attendance history",
    description="Retrieve chronological attendance records for an employee by human-facing employee_id or internal PK.",
)
def get_employee_attendance(
    employee_id: str,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    start_date: Optional[date] = Query(None, description="Start date filter (inclusive)"),
    end_date: Optional[date] = Query(None, description="End date filter (inclusive)"),
    sort_order: str = Query("desc", description="Sort order by date: 'asc' or 'desc'"),
    db: Session = Depends(get_db),
):
    """Fetch attendance history for an employee."""
    return attendance_service.get_employee_attendance_history(
        db=db,
        employee_identifier=employee_id,
        page=page,
        page_size=page_size,
        start_date=start_date,
        end_date=end_date,
        sort_order=sort_order,
    )
