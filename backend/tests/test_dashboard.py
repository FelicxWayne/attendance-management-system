from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.dependencies import get_current_user, get_db
from app.core.security import create_access_token, hash_password
from app.db.database import Base
from app.db.models.attendance import Attendance
from app.db.models.department import Department
from app.db.models.employee import Employee, EmployeeStatus
from app.db.models.user import User, UserRole
from app.main import app

TZ = ZoneInfo("Asia/Kolkata")

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

client = TestClient(app)


def get_auth_header(role: str = "ADMIN", user_id: int = 1) -> dict:
    """Generate HTTP Authorization Bearer header for testing."""
    token = create_access_token(data={"sub": str(user_id), "role": role})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def setup_test_db():
    """Setup and teardown in-memory SQLite schema."""
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    db = TestingSessionLocal()
    # Seed default ADMIN and HR users
    admin_user = User(
        id=1,
        username="admin_user",
        password_hash=hash_password("AdminSecret123!"),
        role=UserRole.ADMIN.value,
    )
    hr_user = User(
        id=2,
        username="hr_user",
        password_hash=hash_password("HrSecret123!"),
        role=UserRole.HR.value,
    )
    db.add(admin_user)
    db.add(hr_user)
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=test_engine)
    app.dependency_overrides.clear()


# ============================================================================
# 1. AUTHENTICATION & RBAC TESTS
# ============================================================================

def test_dashboard_unauthenticated_returns_401():
    """Unauthenticated request to GET /api/v1/dashboard must return HTTP 401."""
    response = client.get("/api/v1/dashboard")
    assert response.status_code == 401
    assert "detail" in response.json()


def test_dashboard_authenticated_admin_returns_200():
    """Authenticated ADMIN user must be permitted (HTTP 200)."""
    response = client.get("/api/v1/dashboard", headers=get_auth_header("ADMIN"))
    assert response.status_code == 200
    data = response.json()
    assert "total_employees" in data
    assert "active_employees" in data
    assert "present_today" in data
    assert "absent_today" in data
    assert "department_counts" in data


def test_dashboard_authenticated_hr_returns_200():
    """Authenticated HR user must be permitted (HTTP 200)."""
    response = client.get("/api/v1/dashboard", headers=get_auth_header("HR", user_id=2))
    assert response.status_code == 200
    data = response.json()
    assert data["total_employees"] == 0
    assert data["active_employees"] == 0


def test_dashboard_unsupported_role_returns_403():
    """Authenticated user with non-ADMIN/HR role (e.g., EMPLOYEE) must return HTTP 403."""
    dummy_user = User(
        id=99,
        username="emp_user",
        password_hash="dummy",
        role="EMPLOYEE",
    )
    app.dependency_overrides[get_current_user] = lambda: dummy_user
    try:
        response = client.get("/api/v1/dashboard", headers={"Authorization": "Bearer dummy_token"})
        assert response.status_code == 403
        assert response.json()["detail"] == "Operation not permitted for current role"
    finally:
        app.dependency_overrides.pop(get_current_user, None)



# ============================================================================
# 2. ZERO-DATA / EMPTY DATABASE TESTS
# ============================================================================

def test_dashboard_completely_empty_db():
    """When no departments or employees exist, returns all zeros and empty list."""
    response = client.get("/api/v1/dashboard", headers=get_auth_header("ADMIN"))
    assert response.status_code == 200
    assert response.json() == {
        "total_employees": 0,
        "active_employees": 0,
        "present_today": 0,
        "absent_today": 0,
        "department_counts": [],
    }


def test_dashboard_department_with_zero_employees():
    """Departments with no employees should be included with employee_count = 0."""
    db = TestingSessionLocal()
    d1 = Department(id=1, name="Finance")
    d2 = Department(id=2, name="Engineering")
    db.add_all([d1, d2])
    db.commit()
    db.close()

    response = client.get("/api/v1/dashboard", headers=get_auth_header("ADMIN"))
    assert response.status_code == 200
    data = response.json()
    assert data["total_employees"] == 0
    assert data["active_employees"] == 0
    assert data["present_today"] == 0
    assert data["absent_today"] == 0
    # Deterministic alphabetical ordering: Engineering, then Finance
    assert len(data["department_counts"]) == 2
    assert data["department_counts"][0] == {
        "department_id": 2,
        "department_name": "Engineering",
        "employee_count": 0,
    }
    assert data["department_counts"][1] == {
        "department_id": 1,
        "department_name": "Finance",
        "employee_count": 0,
    }


# ============================================================================
# 3. CORE EMPLOYEE COUNT TESTS (ACTIVE vs INACTIVE)
# ============================================================================

def test_dashboard_employee_counts_active_and_inactive():
    """Total employees includes both active and inactive; active count strictly includes only active."""
    db = TestingSessionLocal()
    dept = Department(id=1, name="Engineering")
    db.add(dept)

    # 3 active employees, 2 inactive employees
    for i in range(1, 4):
        db.add(
            Employee(
                id=i,
                employee_id=f"EMP-00{i}",
                name=f"Active Worker {i}",
                email=f"active{i}@example.com",
                department_id=1,
                designation="Developer",
                status=EmployeeStatus.ACTIVE.value,
            )
        )
    for i in range(4, 6):
        db.add(
            Employee(
                id=i,
                employee_id=f"EMP-00{i}",
                name=f"Inactive Worker {i}",
                email=f"inactive{i}@example.com",
                department_id=1,
                designation="Contractor",
                status=EmployeeStatus.INACTIVE.value,
            )
        )
    db.commit()
    db.close()

    response = client.get("/api/v1/dashboard", headers=get_auth_header("ADMIN"))
    assert response.status_code == 200
    data = response.json()
    assert data["total_employees"] == 5
    assert data["active_employees"] == 3
    # No attendance yet, so all active employees are absent
    assert data["present_today"] == 0
    assert data["absent_today"] == 3
    # Department count includes both active and inactive employees (total distribution = 5)
    assert data["department_counts"] == [
        {
            "department_id": 1,
            "department_name": "Engineering",
            "employee_count": 5,
        }
    ]


# ============================================================================
# 4. ATTENDANCE METRIC TESTS (PRESENT, ABSENT, CHECKOUT NULL, TIMEZONE)
# ============================================================================

def test_dashboard_attendance_present_and_absent_today():
    """Active employee with attendance today is present; active without attendance is absent."""
    db = TestingSessionLocal()
    dept = Department(id=1, name="Operations")
    db.add(dept)

    emp1 = Employee(
        id=1,
        employee_id="EMP-101",
        name="Alice",
        email="alice@example.com",
        department_id=1,
        designation="Lead",
        status=EmployeeStatus.ACTIVE.value,
    )
    emp2 = Employee(
        id=2,
        employee_id="EMP-102",
        name="Bob",
        email="bob@example.com",
        department_id=1,
        designation="Specialist",
        status=EmployeeStatus.ACTIVE.value,
    )
    db.add_all([emp1, emp2])

    test_date = date(2026, 9, 5)
    # Alice is checked in today
    att1 = Attendance(
        id=1,
        employee_id=1,
        attendance_date=test_date,
        check_in=datetime(2026, 9, 5, 9, 30, 0, tzinfo=TZ),
        check_out=datetime(2026, 9, 5, 17, 30, 0, tzinfo=TZ),
    )
    db.add(att1)
    db.commit()
    db.close()

    # Query dashboard for test_date
    response = client.get(f"/api/v1/dashboard?date={test_date.isoformat()}", headers=get_auth_header("ADMIN"))
    assert response.status_code == 200
    data = response.json()
    assert data["total_employees"] == 2
    assert data["active_employees"] == 2
    assert data["present_today"] == 1  # Alice
    assert data["absent_today"] == 1   # Bob


def test_dashboard_attendance_with_null_checkout_is_present():
    """Employee with check-in and check_out=NULL must still be counted as PRESENT."""
    db = TestingSessionLocal()
    dept = Department(id=1, name="IT")
    db.add(dept)

    emp = Employee(
        id=1,
        employee_id="EMP-201",
        name="Charlie",
        email="charlie@example.com",
        department_id=1,
        designation="Sysadmin",
        status=EmployeeStatus.ACTIVE.value,
    )
    db.add(emp)

    test_date = date(2026, 9, 5)
    att = Attendance(
        id=1,
        employee_id=1,
        attendance_date=test_date,
        check_in=datetime(2026, 9, 5, 9, 0, 0, tzinfo=TZ),
        check_out=None,  # Not checked out yet
    )
    db.add(att)
    db.commit()
    db.close()

    response = client.get(f"/api/v1/dashboard?date={test_date.isoformat()}", headers=get_auth_header("ADMIN"))
    assert response.status_code == 200
    data = response.json()
    assert data["present_today"] == 1
    assert data["absent_today"] == 0


def test_dashboard_yesterday_attendance_does_not_count_as_present_today():
    """Attendance from yesterday must not make an employee present today."""
    db = TestingSessionLocal()
    dept = Department(id=1, name="IT")
    db.add(dept)

    emp = Employee(
        id=1,
        employee_id="EMP-301",
        name="David",
        email="david@example.com",
        department_id=1,
        designation="Dev",
        status=EmployeeStatus.ACTIVE.value,
    )
    db.add(emp)

    yesterday = date(2026, 9, 4)
    today = date(2026, 9, 5)
    att = Attendance(
        id=1,
        employee_id=1,
        attendance_date=yesterday,
        check_in=datetime(2026, 9, 4, 9, 0, 0, tzinfo=TZ),
        check_out=datetime(2026, 9, 4, 18, 0, 0, tzinfo=TZ),
    )
    db.add(att)
    db.commit()
    db.close()

    response = client.get(f"/api/v1/dashboard?date={today.isoformat()}", headers=get_auth_header("ADMIN"))
    assert response.status_code == 200
    data = response.json()
    assert data["present_today"] == 0
    assert data["absent_today"] == 1


def test_dashboard_inactive_employee_attendance_excluded_from_present_today():
    """Inactive employee with an attendance record today MUST NOT increase present_today or absent_today."""
    db = TestingSessionLocal()
    dept = Department(id=1, name="HR")
    db.add(dept)

    # 1 Active employee (no attendance)
    emp_active = Employee(
        id=1,
        employee_id="EMP-ACT",
        name="Active Emily",
        email="emily@example.com",
        department_id=1,
        designation="Recruiter",
        status=EmployeeStatus.ACTIVE.value,
    )
    # 1 Inactive employee (has attendance today)
    emp_inactive = Employee(
        id=2,
        employee_id="EMP-INA",
        name="Inactive Frank",
        email="frank@example.com",
        department_id=1,
        designation="Former Lead",
        status=EmployeeStatus.INACTIVE.value,
    )
    db.add_all([emp_active, emp_inactive])

    today = date(2026, 9, 5)
    att_inactive = Attendance(
        id=1,
        employee_id=2,  # Belongs to INACTIVE employee
        attendance_date=today,
        check_in=datetime(2026, 9, 5, 9, 0, 0, tzinfo=TZ),
        check_out=datetime(2026, 9, 5, 17, 0, 0, tzinfo=TZ),
    )
    db.add(att_inactive)
    db.commit()
    db.close()

    response = client.get(f"/api/v1/dashboard?date={today.isoformat()}", headers=get_auth_header("ADMIN"))
    assert response.status_code == 200
    data = response.json()
    assert data["total_employees"] == 2
    assert data["active_employees"] == 1
    # Active Emily has no attendance => present_today = 0, absent_today = 1
    # Inactive Frank's attendance record MUST NOT count towards present_today
    assert data["present_today"] == 0
    assert data["absent_today"] == 1


def test_dashboard_future_attendance_does_not_affect_today():
    """Attendance for a future date must not be counted in today's metrics."""
    db = TestingSessionLocal()
    dept = Department(id=1, name="Finance")
    db.add(dept)

    emp = Employee(
        id=1,
        employee_id="EMP-FUT",
        name="Grace",
        email="grace@example.com",
        department_id=1,
        designation="Analyst",
        status=EmployeeStatus.ACTIVE.value,
    )
    db.add(emp)

    today = date(2026, 9, 5)
    tomorrow = date(2026, 9, 6)
    att = Attendance(
        id=1,
        employee_id=1,
        attendance_date=tomorrow,
        check_in=datetime(2026, 9, 6, 9, 0, 0, tzinfo=TZ),
        check_out=datetime(2026, 9, 6, 17, 0, 0, tzinfo=TZ),
    )
    db.add(att)
    db.commit()
    db.close()

    response = client.get(f"/api/v1/dashboard?date={today.isoformat()}", headers=get_auth_header("ADMIN"))
    assert response.status_code == 200
    data = response.json()
    assert data["present_today"] == 0
    assert data["absent_today"] == 1


# ============================================================================
# 5. DEPARTMENT-WISE DISTRIBUTION TESTS
# ============================================================================

def test_dashboard_department_counts_multiple_and_ordering():
    """Verify department counts include inactive employees, represent 0-employee departments, and sort alphabetically."""
    db = TestingSessionLocal()
    d_eng = Department(id=1, name="Engineering")
    d_qa = Department(id=2, name="Quality Assurance")
    d_hr = Department(id=3, name="Human Resources")
    d_empty = Department(id=4, name="Analytics")
    db.add_all([d_eng, d_qa, d_hr, d_empty])

    # Engineering: 2 active, 1 inactive = 3
    db.add(Employee(id=1, employee_id="E1", name="E1", email="e1@co.com", department_id=1, designation="D", status=EmployeeStatus.ACTIVE.value))
    db.add(Employee(id=2, employee_id="E2", name="E2", email="e2@co.com", department_id=1, designation="D", status=EmployeeStatus.ACTIVE.value))
    db.add(Employee(id=3, employee_id="E3", name="E3", email="e3@co.com", department_id=1, designation="D", status=EmployeeStatus.INACTIVE.value))

    # Quality Assurance: 1 active = 1
    db.add(Employee(id=4, employee_id="E4", name="E4", email="e4@co.com", department_id=2, designation="D", status=EmployeeStatus.ACTIVE.value))

    # Human Resources: 1 inactive = 1
    db.add(Employee(id=5, employee_id="E5", name="E5", email="e5@co.com", department_id=3, designation="D", status=EmployeeStatus.INACTIVE.value))

    # Analytics: 0 employees = 0
    db.commit()
    db.close()

    response = client.get("/api/v1/dashboard", headers=get_auth_header("ADMIN"))
    assert response.status_code == 200
    data = response.json()
    assert data["total_employees"] == 5
    assert data["active_employees"] == 3

    dept_counts = data["department_counts"]
    assert len(dept_counts) == 4

    # Alphabetical order: Analytics, Engineering, Human Resources, Quality Assurance
    assert dept_counts[0] == {"department_id": 4, "department_name": "Analytics", "employee_count": 0}
    assert dept_counts[1] == {"department_id": 1, "department_name": "Engineering", "employee_count": 3}
    assert dept_counts[2] == {"department_id": 3, "department_name": "Human Resources", "employee_count": 1}
    assert dept_counts[3] == {"department_id": 2, "department_name": "Quality Assurance", "employee_count": 1}


# ============================================================================
# 6. TIMEZONE & DEFAULT DATE TESTS
# ============================================================================

def test_dashboard_default_date_uses_asia_kolkata():
    """When date query param is omitted, dashboard correctly defaults to today in Asia/Kolkata."""
    today_kolkata = datetime.now(TZ).date()

    db = TestingSessionLocal()
    dept = Department(id=1, name="Support")
    db.add(dept)

    emp = Employee(
        id=1,
        employee_id="EMP-KOL",
        name="Kolkata User",
        email="kolkata@example.com",
        department_id=1,
        designation="Agent",
        status=EmployeeStatus.ACTIVE.value,
    )
    db.add(emp)

    att = Attendance(
        id=1,
        employee_id=1,
        attendance_date=today_kolkata,
        check_in=datetime.now(TZ),
        check_out=None,
    )
    db.add(att)
    db.commit()
    db.close()

    # Omit date parameter to exercise today_in_business_tz() default
    response = client.get("/api/v1/dashboard", headers=get_auth_header("ADMIN"))
    assert response.status_code == 200
    data = response.json()
    assert data["total_employees"] == 1
    assert data["active_employees"] == 1
    assert data["present_today"] == 1
    assert data["absent_today"] == 0
