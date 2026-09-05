from typing import Any, Dict, Optional
from fastapi import HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.db.models.department import Department
from app.db.models.employee import Employee, EmployeeStatus
from app.schemas.employee import EmployeeCreate, EmployeeUpdate


class EmployeeService:
    """Business service handling lifecycle, search, pagination, and persistence for employees."""

    # Whitelist of allowed sortable columns to prevent arbitrary SQL/order-by injection
    SORTABLE_FIELDS = {
        "employee_id": Employee.employee_id,
        "name": Employee.name,
        "created_at": Employee.created_at,
    }

    @classmethod
    def get_employee_by_id(cls, db: Session, employee_id: int) -> Employee:
        """Fetch employee by primary key with eagerly loaded department.

        Raises HTTP 404 if employee does not exist.
        """
        employee = (
            db.query(Employee)
            .options(joinedload(Employee.department))
            .filter(Employee.id == employee_id)
            .first()
        )
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee with ID {employee_id} not found",
            )
        return employee

    @classmethod
    def create_employee(cls, db: Session, employee_in: EmployeeCreate) -> Employee:
        """Create a new employee entity with default ACTIVE status.

        Validates department existence and enforces uniqueness on employee_id
        and lower(email).
        """
        # 1. Validate department existence
        department = (
            db.query(Department)
            .filter(Department.id == employee_in.department_id)
            .first()
        )
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Department with ID {employee_in.department_id} not found",
            )

        # 2. Check employee_id uniqueness
        existing_id = (
            db.query(Employee)
            .filter(Employee.employee_id == employee_in.employee_id)
            .first()
        )
        if existing_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Employee with ID '{employee_in.employee_id}' already exists",
            )

        # 3. Check case-insensitive email uniqueness
        existing_email = (
            db.query(Employee)
            .filter(func.lower(Employee.email) == employee_in.email.lower())
            .first()
        )
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Employee with email '{employee_in.email}' already exists",
            )

        # 4. Instantiate employee defaulting to ACTIVE status
        employee = Employee(
            employee_id=employee_in.employee_id,
            name=employee_in.name,
            email=employee_in.email,
            mobile=employee_in.mobile,
            department_id=employee_in.department_id,
            designation=employee_in.designation,
            status=EmployeeStatus.ACTIVE.value,
        )
        db.add(employee)

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Employee ID or email conflicts with an existing record",
            )

        # Ensure relationships are loaded for response serialization
        db.refresh(employee)
        return employee

    @classmethod
    def list_employees(
        cls,
        db: Session,
        page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None,
        status_filter: Optional[EmployeeStatus] = None,
        department_id: Optional[int] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Dict[str, Any]:
        """Search, filter, sort, and paginate employee records safely.

        Only whitelisted sort fields ('employee_id', 'name', 'created_at') are accepted.
        Search operates case-insensitively across employee_id, name, and email.
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

        # 2. Build base query
        query = db.query(Employee)

        # 3. Apply search filter across employee_id, name, and email
        if search and search.strip():
            pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Employee.employee_id.ilike(pattern),
                    Employee.name.ilike(pattern),
                    Employee.email.ilike(pattern),
                )
            )

        # 4. Apply status filter
        if status_filter is not None:
            status_val = (
                status_filter.value
                if isinstance(status_filter, EmployeeStatus)
                else str(status_filter)
            )
            query = query.filter(Employee.status == status_val)

        # 5. Apply department filter
        if department_id is not None:
            query = query.filter(Employee.department_id == department_id)

        # 6. Calculate total count before pagination
        total = query.count()
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        # 7. Apply ordering
        sort_col = cls.SORTABLE_FIELDS[sort_by]
        order_expr = sort_col.asc() if sort_order_clean == "asc" else sort_col.desc()
        query = query.order_by(order_expr)

        # 8. Apply pagination with eager loading of department relationship
        offset = (page - 1) * page_size
        items = (
            query.options(joinedload(Employee.department))
            .offset(offset)
            .limit(page_size)
            .all()
        )

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    @classmethod
    def update_employee(
        cls,
        db: Session,
        employee_id: int,
        employee_in: EmployeeUpdate,
    ) -> Employee:
        """Update existing employee details and status.

        Allows keeping own employee_id and email, but rejects conflicts with
        other employee records.
        """
        # 1. Verify employee exists
        employee = (
            db.query(Employee)
            .options(joinedload(Employee.department))
            .filter(Employee.id == employee_id)
            .first()
        )
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee with ID {employee_id} not found",
            )

        # 2. Verify target department exists
        department = (
            db.query(Department)
            .filter(Department.id == employee_in.department_id)
            .first()
        )
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Department with ID {employee_in.department_id} not found",
            )

        # 3. Check employee_id uniqueness excluding current employee
        conflict_id = (
            db.query(Employee)
            .filter(
                Employee.id != employee_id,
                Employee.employee_id == employee_in.employee_id,
            )
            .first()
        )
        if conflict_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Employee with ID '{employee_in.employee_id}' already exists",
            )

        # 4. Check case-insensitive email uniqueness excluding current employee
        conflict_email = (
            db.query(Employee)
            .filter(
                Employee.id != employee_id,
                func.lower(Employee.email) == employee_in.email.lower(),
            )
            .first()
        )
        if conflict_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Employee with email '{employee_in.email}' already exists",
            )

        # 5. Apply updates
        employee.employee_id = employee_in.employee_id
        employee.name = employee_in.name
        employee.email = employee_in.email
        employee.mobile = employee_in.mobile
        employee.department_id = employee_in.department_id
        employee.designation = employee_in.designation
        employee.status = (
            employee_in.status.value
            if isinstance(employee_in.status, EmployeeStatus)
            else str(employee_in.status)
        )

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Employee ID or email conflicts with an existing record",
            )

        db.refresh(employee)
        return employee

    @classmethod
    def deactivate_employee(cls, db: Session, employee_id: int) -> Employee:
        """Logically deactivate an employee by setting status to INACTIVE.

        Preserves database row, historical attendances, and department links.
        Operates idempotently if already INACTIVE.
        """
        employee = (
            db.query(Employee)
            .options(joinedload(Employee.department))
            .filter(Employee.id == employee_id)
            .first()
        )
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee with ID {employee_id} not found",
            )

        employee.status = EmployeeStatus.INACTIVE.value
        db.commit()
        db.refresh(employee)
        return employee


employee_service = EmployeeService()
