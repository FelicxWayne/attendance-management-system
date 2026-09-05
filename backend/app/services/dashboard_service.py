from datetime import date, datetime
from typing import Optional
from zoneinfo import ZoneInfo
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models.attendance import Attendance
from app.db.models.department import Department
from app.db.models.employee import Employee, EmployeeStatus
from app.schemas.dashboard import DashboardResponse, DepartmentEmployeeCount

# Application business timezone: Asia/Kolkata
BUSINESS_TZ = ZoneInfo("Asia/Kolkata")


class DashboardService:
    """Service encapsulating aggregated business metrics for operational reporting."""

    @staticmethod
    def today_in_business_tz() -> date:
        """Return the current calendar date in Asia/Kolkata timezone."""
        return datetime.now(BUSINESS_TZ).date()

    @classmethod
    def get_dashboard_metrics(
        cls,
        db: Session,
        target_date: Optional[date] = None,
    ) -> DashboardResponse:
        """Calculate and return operational dashboard metrics.

        Business Metric Definitions:
        - total_employees: Total employees in the employees table (ACTIVE + INACTIVE).
        - active_employees: Total employees currently having status = 'ACTIVE'.
        - present_today: Count of ACTIVE employees with an attendance record for target_date.
          (Inactive employees with attendance records are strictly excluded).
        - absent_today: Count of ACTIVE employees without an attendance record for target_date.
          (active_employees - present_today).
        - department_counts: Distribution count of all employees (ACTIVE + INACTIVE) per department.
          Departments with zero employees are retained with employee_count = 0.
          Deterministic ordering by department name ascending.

        Args:
            db: Database session.
            target_date: Optional date to compute metrics for (defaults to today in Asia/Kolkata).

        Returns:
            DashboardResponse containing consolidated metrics.
        """
        current_date = target_date if target_date is not None else cls.today_in_business_tz()

        # 1. Total employees (all employees in the database)
        total_employees = db.query(func.count(Employee.id)).scalar() or 0

        # 2. Active employees (status = 'ACTIVE')
        active_employees = (
            db.query(func.count(Employee.id))
            .filter(Employee.status == EmployeeStatus.ACTIVE.value)
            .scalar()
            or 0
        )

        # 3. Present today: Active employees who have an attendance row for current_date
        # Inactive employees are strictly excluded even if they have an attendance record on that date.
        present_today = (
            db.query(func.count(func.distinct(Attendance.employee_id)))
            .join(Employee, Attendance.employee_id == Employee.id)
            .filter(
                Employee.status == EmployeeStatus.ACTIVE.value,
                Attendance.attendance_date == current_date,
            )
            .scalar()
            or 0
        )

        # 4. Absent today: Active employees who do not have an attendance record for current_date
        absent_today = max(0, active_employees - present_today)

        # 5. Department-wise employee count (distribution of all employees across departments)
        # Using LEFT OUTER JOIN so departments with zero employees still appear with count = 0
        dept_rows = (
            db.query(
                Department.id.label("department_id"),
                Department.name.label("department_name"),
                func.count(Employee.id).label("employee_count"),
            )
            .outerjoin(Employee, Department.id == Employee.department_id)
            .group_by(Department.id, Department.name)
            .order_by(Department.name.asc())
            .all()
        )

        department_counts = [
            DepartmentEmployeeCount(
                department_id=row.department_id,
                department_name=row.department_name,
                employee_count=row.employee_count,
            )
            for row in dept_rows
        ]

        return DashboardResponse(
            total_employees=total_employees,
            active_employees=active_employees,
            present_today=present_today,
            absent_today=absent_today,
            department_counts=department_counts,
        )


dashboard_service = DashboardService()
