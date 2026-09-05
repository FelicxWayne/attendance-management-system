from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.db.models.attendance import Attendance
from app.db.models.department import Department
from app.db.models.employee import Employee, EmployeeStatus
from app.schemas.attendance import (
    AttendanceResponse,
    CheckInRequest,
    CheckOutRequest,
)

# Business timezone: Asia/Kolkata
BUSINESS_TZ = ZoneInfo("Asia/Kolkata")


class AttendanceService:
    """Production service encapsulating attendance check-in, check-out, queries, and business rules."""

    # Whitelist of allowed sortable columns to prevent arbitrary SQL/order-by injection
    SORTABLE_FIELDS = {
        "attendance_date": Attendance.attendance_date,
        "check_in": Attendance.check_in,
        "check_out": Attendance.check_out,
        "created_at": Attendance.created_at,
        "employee_id": Employee.employee_id,
    }

    @staticmethod
    def now_in_business_tz() -> datetime:
        """Return the current timezone-aware timestamp in Asia/Kolkata."""
        return datetime.now(BUSINESS_TZ)

    @staticmethod
    def today_in_business_tz() -> date:
        """Return today's date in Asia/Kolkata."""
        return datetime.now(BUSINESS_TZ).date()

    @staticmethod
    def to_aware(dt: Optional[datetime]) -> Optional[datetime]:
        """Ensure a datetime is timezone-aware in Asia/Kolkata."""
        if dt is None:
            return None
        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            return dt.replace(tzinfo=BUSINESS_TZ)
        return dt.astimezone(BUSINESS_TZ)

    @classmethod
    def resolve_employee(cls, db: Session, employee_identifier: str) -> Employee:
        """Resolve an employee by human-facing employee_id or fallback internal database PK.

        Raises HTTP 404 if the employee does not exist.
        """
        cleaned_id = employee_identifier.strip()
        if not cleaned_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee identifier cannot be empty",
            )

        # 1. Look up by human-facing employee_id (e.g. 'EMP001')
        employee = (
            db.query(Employee)
            .options(joinedload(Employee.department))
            .filter(Employee.employee_id == cleaned_id)
            .first()
        )
        if employee:
            return employee

        # 2. Fallback: check if numeric identifier matches internal employees.id
        if cleaned_id.isdigit():
            employee = (
                db.query(Employee)
                .options(joinedload(Employee.department))
                .filter(Employee.id == int(cleaned_id))
                .first()
            )
            if employee:
                return employee

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with ID '{employee_identifier}' not found",
        )

    @classmethod
    def check_in(cls, db: Session, payload: CheckInRequest) -> Attendance:
        """Mark/check-in an employee for attendance on a given date.

        Enforces:
        - Employee exists
        - Employee is ACTIVE
        - Check-in timestamp and attendance_date cannot be in the future
        - check_in must be timezone-aware and match attendance_date in Asia/Kolkata
        - No duplicate attendance for same (employee_id, attendance_date)
        - DB IntegrityError caught and translated to HTTP 409
        """
        # 1. Resolve employee
        employee = cls.resolve_employee(db, payload.employee_id)

        # 2. Verify active status
        if employee.status != EmployeeStatus.ACTIVE.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot mark attendance for inactive employee '{employee.employee_id}'",
            )

        # 3. Process timestamps in Asia/Kolkata
        current_now = cls.now_in_business_tz()
        current_today = current_now.date()

        if payload.check_in is not None:
            if payload.check_in.tzinfo is None or payload.check_in.tzinfo.utcoffset(payload.check_in) is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="check_in timestamp must be timezone-aware (e.g. 2026-09-05T09:30:00+05:30)",
                )
            check_in_dt = payload.check_in.astimezone(BUSINESS_TZ)
        else:
            check_in_dt = current_now

        # Guard against future check-in timestamp (allow 60s tolerance for minor clock skew)
        if check_in_dt > current_now + timedelta(seconds=60):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="check_in timestamp cannot be in the future",
            )

        # Resolve attendance_date
        target_date = payload.attendance_date if payload.attendance_date is not None else check_in_dt.date()

        # Guard against future attendance_date
        if target_date > current_today:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"attendance_date ({target_date}) cannot be in the future",
            )

        # Ensure local date of check_in in Asia/Kolkata corresponds to attendance_date
        if check_in_dt.date() != target_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"attendance_date ({target_date}) does not match the local date "
                    f"of check_in ({check_in_dt.date()}) in Asia/Kolkata"
                ),
            )

        # 4. Check for existing attendance record (application-level check)
        existing = (
            db.query(Attendance)
            .filter(
                Attendance.employee_id == employee.id,
                Attendance.attendance_date == target_date,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Attendance record already exists for employee '{employee.employee_id}' on date {target_date}",
            )

        # 5. Persist attendance record
        attendance = Attendance(
            employee_id=employee.id,
            attendance_date=target_date,
            check_in=check_in_dt,
        )
        db.add(attendance)

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Attendance record already exists for employee '{employee.employee_id}' on date {target_date}",
            )

        db.refresh(attendance)
        # Eagerly load relationship for response serialization
        attendance = (
            db.query(Attendance)
            .options(joinedload(Attendance.employee).joinedload(Employee.department))
            .filter(Attendance.id == attendance.id)
            .first()
        )
        return attendance

    @classmethod
    def check_out(cls, db: Session, payload: CheckOutRequest) -> Attendance:
        """Record check-out for an existing attendance record.

        Enforces:
        - Employee exists
        - Attendance record exists for target attendance_date
        - Employee cannot check out twice
        - check_out must be strictly later than check_in
        - check_out must be timezone-aware and correspond to attendance_date in Asia/Kolkata
        - check_out cannot be in the future
        """
        # 1. Resolve employee
        employee = cls.resolve_employee(db, payload.employee_id)

        # 2. Process timestamps in Asia/Kolkata
        current_now = cls.now_in_business_tz()

        if payload.check_out is not None:
            if payload.check_out.tzinfo is None or payload.check_out.tzinfo.utcoffset(payload.check_out) is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="check_out timestamp must be timezone-aware (e.g. 2026-09-05T18:00:00+05:30)",
                )
            check_out_dt = payload.check_out.astimezone(BUSINESS_TZ)
        else:
            check_out_dt = current_now

        # Guard against future check-out timestamp
        if check_out_dt > current_now + timedelta(seconds=60):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="check_out timestamp cannot be in the future",
            )

        # Resolve attendance_date
        target_date = payload.attendance_date if payload.attendance_date is not None else check_out_dt.date()

        # Date consistency
        if check_out_dt.date() != target_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"check_out timestamp date ({check_out_dt.date()}) does not correspond "
                    f"to attendance_date ({target_date}) in Asia/Kolkata"
                ),
            )

        # 3. Retrieve existing attendance record
        attendance = (
            db.query(Attendance)
            .options(joinedload(Attendance.employee).joinedload(Employee.department))
            .filter(
                Attendance.employee_id == employee.id,
                Attendance.attendance_date == target_date,
            )
            .first()
        )
        if not attendance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Attendance record not found for employee '{employee.employee_id}' "
                    f"on date {target_date}. Employee has not checked in."
                ),
            )

        # 4. Check if already checked out
        if attendance.check_out is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Employee '{employee.employee_id}' has already checked out for date {target_date}",
            )

        # 5. Check chronological ordering (check_out > check_in)
        check_in_aware = cls.to_aware(attendance.check_in)
        if check_out_dt <= check_in_aware:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="check_out time must be strictly after check_in time",
            )

        # 6. Apply check_out
        attendance.check_out = check_out_dt

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database integrity constraint violated during check-out",
            )

        db.refresh(attendance)
        return attendance

    @classmethod
    def check_out_by_id(
        cls,
        db: Session,
        attendance_id: int,
        check_out: Optional[datetime] = None,
    ) -> Attendance:
        """Check out an attendance record by its primary key ID."""
        attendance = (
            db.query(Attendance)
            .options(joinedload(Attendance.employee).joinedload(Employee.department))
            .filter(Attendance.id == attendance_id)
            .first()
        )
        if not attendance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Attendance record with ID {attendance_id} not found",
            )

        current_now = cls.now_in_business_tz()

        if check_out is not None:
            if check_out.tzinfo is None or check_out.tzinfo.utcoffset(check_out) is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="check_out timestamp must be timezone-aware",
                )
            check_out_dt = check_out.astimezone(BUSINESS_TZ)
        else:
            check_out_dt = current_now

        if check_out_dt > current_now + timedelta(seconds=60):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="check_out timestamp cannot be in the future",
            )

        if check_out_dt.date() != attendance.attendance_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"check_out timestamp date ({check_out_dt.date()}) does not correspond "
                    f"to attendance record date ({attendance.attendance_date}) in Asia/Kolkata"
                ),
            )

        if attendance.check_out is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Attendance record {attendance_id} already has check-out recorded",
            )

        check_in_aware = cls.to_aware(attendance.check_in)
        if check_out_dt <= check_in_aware:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="check_out time must be strictly after check_in time",
            )

        attendance.check_out = check_out_dt
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database integrity constraint violated during check-out",
            )

        db.refresh(attendance)
        return attendance

    @classmethod
    def list_attendance(
        cls,
        db: Session,
        page: int = 1,
        page_size: int = 10,
        attendance_date: Optional[date] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        employee_id: Optional[str] = None,
        department_id: Optional[int] = None,
        include_absent: bool = False,
        sort_by: str = "attendance_date",
        sort_order: str = "desc",
    ) -> Dict[str, Any]:
        """Retrieve paginated attendance records with filtering and deterministic sorting.

        Preserves historical attendance records for inactive employees.
        If include_absent=True and attendance_date is specified, computes PRESENT and ABSENT
        status across active employees for that date.
        """
        # 1. Validate sorting parameters
        if sort_by not in cls.SORTABLE_FIELDS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid sort field '{sort_by}'. Allowed fields: {', '.join(cls.SORTABLE_FIELDS.keys())}",
            )
        sort_order_clean = sort_order.lower()
        if sort_order_clean not in ("asc", "desc"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid sort order '{sort_order}'. Allowed values: 'asc', 'desc'",
            )

        # 2. Validate date range
        if start_date and end_date and start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"start_date ({start_date}) cannot be after end_date ({end_date})",
            )

        # 3. Special Case: Daily attendance with computed ABSENT status
        if include_absent and attendance_date is not None:
            return cls._list_with_absent(
                db=db,
                page=page,
                page_size=page_size,
                attendance_date=attendance_date,
                employee_id=employee_id,
                department_id=department_id,
            )

        # 4. Standard Attendance query
        query = (
            db.query(Attendance)
            .join(Employee, Attendance.employee_id == Employee.id)
            .options(
                joinedload(Attendance.employee).joinedload(Employee.department)
            )
        )

        # Filter by single date
        if attendance_date is not None:
            query = query.filter(Attendance.attendance_date == attendance_date)

        # Filter by date range
        if start_date is not None:
            query = query.filter(Attendance.attendance_date >= start_date)
        if end_date is not None:
            query = query.filter(Attendance.attendance_date <= end_date)

        # Filter by employee_id (human-facing or internal)
        if employee_id and employee_id.strip():
            emp_clean = employee_id.strip()
            if emp_clean.isdigit():
                query = query.filter(
                    (Employee.employee_id == emp_clean) | (Employee.id == int(emp_clean))
                )
            else:
                query = query.filter(Employee.employee_id == emp_clean)

        # Filter by department_id
        if department_id is not None:
            query = query.filter(Employee.department_id == department_id)

        # Calculate count before pagination
        total = query.count()
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        # Apply sorting
        sort_col = cls.SORTABLE_FIELDS[sort_by]
        order_expr = sort_col.asc() if sort_order_clean == "asc" else sort_col.desc()
        query = query.order_by(order_expr, Attendance.id.desc())

        # Paginate
        offset = (page - 1) * page_size
        records = query.offset(offset).limit(page_size).all()

        items = [AttendanceResponse.model_validate(rec) for rec in records]

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    @classmethod
    def _list_with_absent(
        cls,
        db: Session,
        page: int,
        page_size: int,
        attendance_date: date,
        employee_id: Optional[str] = None,
        department_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Compute full attendance status (PRESENT / ABSENT) for ACTIVE employees on a date."""
        query = (
            db.query(Employee, Attendance)
            .outerjoin(
                Attendance,
                (Employee.id == Attendance.employee_id)
                & (Attendance.attendance_date == attendance_date),
            )
            .options(joinedload(Employee.department))
            .filter(Employee.status == EmployeeStatus.ACTIVE.value)
        )

        if employee_id and employee_id.strip():
            emp_clean = employee_id.strip()
            if emp_clean.isdigit():
                query = query.filter(
                    (Employee.employee_id == emp_clean) | (Employee.id == int(emp_clean))
                )
            else:
                query = query.filter(Employee.employee_id == emp_clean)

        if department_id is not None:
            query = query.filter(Employee.department_id == department_id)

        total = query.count()
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        offset = (page - 1) * page_size
        results = (
            query.order_by(Employee.employee_id.asc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        items: List[AttendanceResponse] = []
        for emp, att in results:
            dept_name = emp.department.name if emp.department else None
            if att is not None:
                items.append(
                    AttendanceResponse(
                        id=att.id,
                        employee_id=emp.employee_id,
                        employee_name=emp.name,
                        department_name=dept_name,
                        attendance_date=attendance_date,
                        check_in=att.check_in,
                        check_out=att.check_out,
                        status="PRESENT",
                    )
                )
            else:
                items.append(
                    AttendanceResponse(
                        id=None,
                        employee_id=emp.employee_id,
                        employee_name=emp.name,
                        department_name=dept_name,
                        attendance_date=attendance_date,
                        check_in=None,
                        check_out=None,
                        status="ABSENT",
                    )
                )

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    @classmethod
    def get_employee_attendance_history(
        cls,
        db: Session,
        employee_identifier: str,
        page: int = 1,
        page_size: int = 10,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        sort_order: str = "desc",
    ) -> Dict[str, Any]:
        """Retrieve attendance history for a single employee.

        Works for both ACTIVE and INACTIVE employees so historical records remain accessible.
        Raises HTTP 404 if the employee does not exist.
        """
        # Resolve employee (allows historical lookups for inactive staff)
        employee = cls.resolve_employee(db, employee_identifier)

        if start_date and end_date and start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"start_date ({start_date}) cannot be after end_date ({end_date})",
            )

        sort_order_clean = sort_order.lower()
        if sort_order_clean not in ("asc", "desc"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid sort order '{sort_order}'. Allowed values: 'asc', 'desc'",
            )

        query = (
            db.query(Attendance)
            .options(
                joinedload(Attendance.employee).joinedload(Employee.department)
            )
            .filter(Attendance.employee_id == employee.id)
        )

        if start_date is not None:
            query = query.filter(Attendance.attendance_date >= start_date)
        if end_date is not None:
            query = query.filter(Attendance.attendance_date <= end_date)

        total = query.count()
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        order_expr = (
            Attendance.attendance_date.asc()
            if sort_order_clean == "asc"
            else Attendance.attendance_date.desc()
        )
        records = (
            query.order_by(order_expr, Attendance.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        items = [AttendanceResponse.model_validate(rec) for rec in records]

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    @classmethod
    def get_daily_status(
        cls,
        db: Session,
        attendance_date: Optional[date] = None,
        department_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> Dict[str, Any]:
        """Compute summary and employee list for a given date with PRESENT and ABSENT counts."""
        target_date = attendance_date or cls.today_in_business_tz()

        # Count total active employees
        base_emp_query = db.query(Employee).filter(Employee.status == EmployeeStatus.ACTIVE.value)
        if department_id is not None:
            base_emp_query = base_emp_query.filter(Employee.department_id == department_id)
        total_active = base_emp_query.count()

        # Count present active employees
        present_count = (
            db.query(Attendance)
            .join(Employee, Attendance.employee_id == Employee.id)
            .filter(
                Employee.status == EmployeeStatus.ACTIVE.value,
                Attendance.attendance_date == target_date,
            )
        )
        if department_id is not None:
            present_count = present_count.filter(Employee.department_id == department_id)
        total_present = present_count.count()
        total_absent = max(0, total_active - total_present)

        paged_data = cls._list_with_absent(
            db=db,
            page=page,
            page_size=page_size,
            attendance_date=target_date,
            department_id=department_id,
        )

        return {
            "attendance_date": target_date,
            "total_active_employees": total_active,
            "present_count": total_present,
            "absent_count": total_absent,
            "items": paged_data["items"],
            "total": paged_data["total"],
            "page": paged_data["page"],
            "page_size": paged_data["page_size"],
            "total_pages": paged_data["total_pages"],
        }


attendance_service = AttendanceService()
