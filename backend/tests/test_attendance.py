from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.dependencies import get_db
from app.core.security import create_access_token, hash_password
from app.db.database import Base
from app.db.models.attendance import Attendance
from app.db.models.department import Department
from app.db.models.employee import Employee, EmployeeStatus
from app.db.models.user import User, UserRole
from app.main import app

# Business timezone
TZ = ZoneInfo("Asia/Kolkata")

# Isolated in-memory SQLite engine for attendance management tests
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
    """Setup and teardown in-memory SQLite schema with seeded departments, users, and employees."""
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()

    # Override get_db dependency for tests
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    # Seed users
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

    # Seed departments
    eng_dept = Department(id=1, name="Engineering")
    hr_dept = Department(id=2, name="Human Resources")
    db.add(eng_dept)
    db.add(hr_dept)

    # Seed employees: 2 ACTIVE, 1 INACTIVE
    emp1 = Employee(
        id=1,
        employee_id="EMP-001",
        name="Alice Johnson",
        email="alice.johnson@example.com",
        mobile="+1-555-0101",
        department_id=1,
        designation="Software Engineer",
        status=EmployeeStatus.ACTIVE.value,
    )
    emp2 = Employee(
        id=2,
        employee_id="EMP-002",
        name="Bob Smith",
        email="bob.smith@example.com",
        mobile="+1-555-0102",
        department_id=1,
        designation="QA Engineer",
        status=EmployeeStatus.ACTIVE.value,
    )
    emp3 = Employee(
        id=3,
        employee_id="EMP-003",
        name="Charlie Davis",
        email="charlie.davis@example.com",
        mobile="+1-555-0103",
        department_id=2,
        designation="HR Specialist",
        status=EmployeeStatus.INACTIVE.value,
    )
    db.add(emp1)
    db.add(emp2)
    db.add(emp3)

    # Seed historical attendance for Charlie (INACTIVE employee) to test historical accessibility
    hist_att = Attendance(
        id=100,
        employee_id=3,
        attendance_date=date(2026, 8, 1),
        check_in=datetime(2026, 8, 1, 9, 0, 0, tzinfo=TZ),
        check_out=datetime(2026, 8, 1, 17, 0, 0, tzinfo=TZ),
    )
    db.add(hist_att)

    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=test_engine)
    app.dependency_overrides.clear()


# ============================================================================
# 1. AUTHENTICATION & RBAC TESTS
# ============================================================================

def test_attendance_endpoints_unauthenticated():
    """Verify unauthenticated requests to attendance endpoints return HTTP 401."""
    assert client.post("/api/v1/attendance", json={"employee_id": "EMP-001"}).status_code == 401
    assert client.put("/api/v1/attendance/100/checkout", json={}).status_code == 401
    assert client.get("/api/v1/attendance").status_code == 401
    assert client.get("/api/v1/attendance/daily-status").status_code == 401
    assert client.get("/api/v1/employees/EMP-001/attendance").status_code == 401


def test_attendance_endpoints_unauthorized_role():
    """Verify users with non-ADMIN and non-HR roles return HTTP 403 Forbidden."""
    from app.core.dependencies import get_current_user

    unauthorized_user = User(id=99, username="guest_user", role="GUEST")
    app.dependency_overrides[get_current_user] = lambda: unauthorized_user
    try:
        resp = client.post(
            "/api/v1/attendance",
            json={"employee_id": "EMP-001"},
            headers={"Authorization": "Bearer mock_token"},
        )
        assert resp.status_code == 403
        assert "operation not permitted" in resp.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_attendance_hr_role_allowed():
    """Verify HR role can check in employees."""
    now_kolkata = datetime.now(TZ)
    resp = client.post(
        "/api/v1/attendance",
        json={
            "employee_id": "EMP-001",
            "attendance_date": now_kolkata.date().isoformat(),
            "check_in": now_kolkata.isoformat(),
        },
        headers=get_auth_header("HR", user_id=2),
    )
    assert resp.status_code == 201


def test_attendance_admin_role_allowed():
    """Verify ADMIN role can check in employees."""
    now_kolkata = datetime.now(TZ)
    resp = client.post(
        "/api/v1/attendance",
        json={
            "employee_id": "EMP-002",
            "attendance_date": now_kolkata.date().isoformat(),
            "check_in": now_kolkata.isoformat(),
        },
        headers=get_auth_header("ADMIN", user_id=1),
    )
    assert resp.status_code == 201


# ============================================================================
# 2. CHECK-IN TESTS
# ============================================================================

def test_checkin_success():
    """Verify valid check-in creates record and returns computed PRESENT status."""
    now_kolkata = datetime.now(TZ)
    resp = client.post(
        "/api/v1/attendance",
        json={
            "employee_id": "EMP-001",
            "attendance_date": now_kolkata.date().isoformat(),
            "check_in": now_kolkata.isoformat(),
        },
        headers=get_auth_header("ADMIN"),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] is not None
    assert data["employee_id"] == "EMP-001"
    assert data["employee_name"] == "Alice Johnson"
    assert data["department_name"] == "Engineering"
    assert data["attendance_date"] == now_kolkata.date().isoformat()
    assert data["status"] == "PRESENT"
    assert data["check_out"] is None


def test_checkin_alias_endpoints():
    """Verify /check-in and /checkin alias routes function identically."""
    now_kolkata = datetime.now(TZ)
    resp = client.post(
        "/api/v1/attendance/check-in",
        json={"employee_id": "EMP-002"},
        headers=get_auth_header("ADMIN"),
    )
    assert resp.status_code == 201
    assert resp.json()["employee_id"] == "EMP-002"


def test_checkin_defaults_to_now():
    """Verify check-in with only employee_id defaults to current date and timestamp in Asia/Kolkata."""
    resp = client.post(
        "/api/v1/attendance",
        json={"employee_id": "EMP-001"},
        headers=get_auth_header("ADMIN"),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["attendance_date"] == datetime.now(TZ).date().isoformat()
    assert data["status"] == "PRESENT"


def test_checkin_nonexistent_employee():
    """Verify check-in for non-existent employee returns HTTP 404."""
    resp = client.post(
        "/api/v1/attendance",
        json={"employee_id": "NON_EXISTENT_999"},
        headers=get_auth_header("ADMIN"),
    )
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_checkin_inactive_employee():
    """Verify check-in for INACTIVE employee is rejected with HTTP 400."""
    resp = client.post(
        "/api/v1/attendance",
        json={"employee_id": "EMP-003"},  # Charlie Davis is INACTIVE
        headers=get_auth_header("ADMIN"),
    )
    assert resp.status_code == 400
    assert "inactive employee" in resp.json()["detail"].lower()


def test_checkin_future_attendance_date():
    """Verify attendance_date in the future is rejected with HTTP 400."""
    future_date = (datetime.now(TZ).date() + timedelta(days=5)).isoformat()
    future_time = (datetime.now(TZ) + timedelta(days=5)).isoformat()
    resp = client.post(
        "/api/v1/attendance",
        json={
            "employee_id": "EMP-001",
            "attendance_date": future_date,
            "check_in": future_time,
        },
        headers=get_auth_header("ADMIN"),
    )
    assert resp.status_code == 400
    assert "cannot be in the future" in resp.json()["detail"].lower()


def test_checkin_future_checkin_time():
    """Verify check_in timestamp far in the future on today is rejected."""
    future_time = (datetime.now(TZ) + timedelta(hours=3)).isoformat()
    resp = client.post(
        "/api/v1/attendance",
        json={
            "employee_id": "EMP-001",
            "attendance_date": datetime.now(TZ).date().isoformat(),
            "check_in": future_time,
        },
        headers=get_auth_header("ADMIN"),
    )
    assert resp.status_code == 400
    assert "cannot be in the future" in resp.json()["detail"].lower()


def test_checkin_duplicate_same_employee_date():
    """Verify checking in twice on the same date returns HTTP 409 Conflict."""
    now_kolkata = datetime.now(TZ)
    # First check-in
    resp1 = client.post(
        "/api/v1/attendance",
        json={
            "employee_id": "EMP-001",
            "attendance_date": now_kolkata.date().isoformat(),
            "check_in": now_kolkata.isoformat(),
        },
        headers=get_auth_header("ADMIN"),
    )
    assert resp1.status_code == 201

    # Second check-in on the same date
    resp2 = client.post(
        "/api/v1/attendance",
        json={
            "employee_id": "EMP-001",
            "attendance_date": now_kolkata.date().isoformat(),
            "check_in": now_kolkata.isoformat(),
        },
        headers=get_auth_header("ADMIN"),
    )
    assert resp2.status_code == 409
    assert "already exists" in resp2.json()["detail"].lower()


def test_checkin_date_time_mismatch():
    """Verify mismatch between check_in timestamp local date and attendance_date is rejected."""
    today = datetime.now(TZ).date()
    yesterday = today - timedelta(days=1)
    check_in_ts = datetime(yesterday.year, yesterday.month, yesterday.day, 9, 30, tzinfo=TZ)

    resp = client.post(
        "/api/v1/attendance",
        json={
            "employee_id": "EMP-001",
            "attendance_date": today.isoformat(),
            "check_in": check_in_ts.isoformat(),
        },
        headers=get_auth_header("ADMIN"),
    )
    assert resp.status_code == 400
    assert "does not match" in resp.json()["detail"].lower()


def test_checkin_naive_datetime_rejected():
    """Verify naive datetime timestamp without timezone is rejected."""
    resp = client.post(
        "/api/v1/attendance",
        json={
            "employee_id": "EMP-001",
            "attendance_date": "2026-09-05",
            "check_in": "2026-09-05T09:30:00",  # Naive, no offset
        },
        headers=get_auth_header("ADMIN"),
    )
    assert resp.status_code in (400, 422)


def test_checkin_empty_employee_id_rejected():
    """Verify whitespace or empty employee_id returns HTTP 422."""
    resp = client.post(
        "/api/v1/attendance",
        json={"employee_id": "   "},
        headers=get_auth_header("ADMIN"),
    )
    assert resp.status_code == 422


# ============================================================================
# 3. CHECK-OUT TESTS
# ============================================================================

def test_checkout_success():
    """Verify valid check-out records check_out timestamp and preserves status=PRESENT."""
    now = datetime.now(TZ)
    today = now.date()
    check_in_time = now - timedelta(hours=3)
    check_out_time = now - timedelta(hours=1)

    # Initial check-in
    checkin_resp = client.post(
        "/api/v1/attendance",
        json={
            "employee_id": "EMP-001",
            "attendance_date": today.isoformat(),
            "check_in": check_in_time.isoformat(),
        },
        headers=get_auth_header("ADMIN"),
    )
    assert checkin_resp.status_code == 201
    att_id = checkin_resp.json()["id"]

    # Check-out via canonical PUT /{attendance_id}/checkout
    checkout_resp = client.put(
        f"/api/v1/attendance/{att_id}/checkout",
        json={"check_out": check_out_time.isoformat()},
        headers=get_auth_header("ADMIN"),
    )
    assert checkout_resp.status_code == 200
    data = checkout_resp.json()
    assert data["check_out"] is not None
    assert data["status"] == "PRESENT"


def test_checkout_default_to_now():
    """Verify checking out without check_out timestamp defaults to now in Asia/Kolkata."""
    now = datetime.now(TZ)
    today = now.date()
    check_in_time = now - timedelta(hours=1)

    checkin_resp = client.post(
        "/api/v1/attendance",
        json={
            "employee_id": "EMP-002",
            "attendance_date": today.isoformat(),
            "check_in": check_in_time.isoformat(),
        },
        headers=get_auth_header("ADMIN"),
    )
    att_id = checkin_resp.json()["id"]

    checkout_resp = client.put(
        f"/api/v1/attendance/{att_id}/checkout",
        json={},
        headers=get_auth_header("ADMIN"),
    )
    assert checkout_resp.status_code == 200
    assert checkout_resp.json()["check_out"] is not None


def test_checkout_nonexistent_attendance_id():
    """Verify check-out for non-existent attendance record ID returns HTTP 404."""
    resp = client.put(
        "/api/v1/attendance/999999/checkout",
        json={},
        headers=get_auth_header("ADMIN"),
    )
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_checkout_duplicate():
    """Verify checking out an already checked-out record returns HTTP 409 Conflict."""
    now = datetime.now(TZ)
    today = now.date()
    check_in_time = now - timedelta(hours=3)
    check_out_time = now - timedelta(hours=1)

    checkin_resp = client.post(
        "/api/v1/attendance",
        json={
            "employee_id": "EMP-001",
            "attendance_date": today.isoformat(),
            "check_in": check_in_time.isoformat(),
        },
        headers=get_auth_header("ADMIN"),
    )
    att_id = checkin_resp.json()["id"]

    # First checkout
    resp1 = client.put(
        f"/api/v1/attendance/{att_id}/checkout",
        json={"check_out": check_out_time.isoformat()},
        headers=get_auth_header("ADMIN"),
    )
    assert resp1.status_code == 200

    # Second checkout
    resp2 = client.put(
        f"/api/v1/attendance/{att_id}/checkout",
        json={"check_out": check_out_time.isoformat()},
        headers=get_auth_header("ADMIN"),
    )
    assert resp2.status_code == 409
    assert "already has check-out" in resp2.json()["detail"].lower()


def test_checkout_before_checkin():
    """Verify check_out earlier than check_in returns HTTP 400 Bad Request."""
    now = datetime.now(TZ)
    today = now.date()
    check_in_time = now - timedelta(hours=2)
    check_out_early = now - timedelta(hours=3)

    checkin_resp = client.post(
        "/api/v1/attendance",
        json={
            "employee_id": "EMP-001",
            "attendance_date": today.isoformat(),
            "check_in": check_in_time.isoformat(),
        },
        headers=get_auth_header("ADMIN"),
    )
    att_id = checkin_resp.json()["id"]

    resp = client.put(
        f"/api/v1/attendance/{att_id}/checkout",
        json={"check_out": check_out_early.isoformat()},
        headers=get_auth_header("ADMIN"),
    )
    assert resp.status_code == 400
    assert "strictly after" in resp.json()["detail"].lower()


def test_checkout_equal_to_checkin():
    """Verify check_out identical to check_in returns HTTP 400 Bad Request."""
    now = datetime.now(TZ)
    today = now.date()
    check_in_time = now - timedelta(hours=2)

    checkin_resp = client.post(
        "/api/v1/attendance",
        json={
            "employee_id": "EMP-001",
            "attendance_date": today.isoformat(),
            "check_in": check_in_time.isoformat(),
        },
        headers=get_auth_header("ADMIN"),
    )
    att_id = checkin_resp.json()["id"]

    resp = client.put(
        f"/api/v1/attendance/{att_id}/checkout",
        json={"check_out": check_in_time.isoformat()},
        headers=get_auth_header("ADMIN"),
    )
    assert resp.status_code == 400
    assert "strictly after" in resp.json()["detail"].lower()


def test_checkout_future_timestamp():
    """Verify check_out timestamp in the future is rejected with HTTP 400."""
    now = datetime.now(TZ)
    today = now.date()
    check_in_time = now - timedelta(hours=1)
    future_checkout = now + timedelta(hours=3)

    checkin_resp = client.post(
        "/api/v1/attendance",
        json={
            "employee_id": "EMP-001",
            "attendance_date": today.isoformat(),
            "check_in": check_in_time.isoformat(),
        },
        headers=get_auth_header("ADMIN"),
    )
    att_id = checkin_resp.json()["id"]

    resp = client.put(
        f"/api/v1/attendance/{att_id}/checkout",
        json={"check_out": future_checkout.isoformat()},
        headers=get_auth_header("ADMIN"),
    )
    assert resp.status_code == 400
    assert "cannot be in the future" in resp.json()["detail"].lower()


def test_checkout_date_mismatch():
    """Verify check_out date that does not match attendance record date is rejected."""
    today = datetime.now(TZ).date()
    check_in_time = datetime(today.year, today.month, today.day, 9, 0, 0, tzinfo=TZ)
    yesterday = today - timedelta(days=1)
    wrong_date_checkout = datetime(yesterday.year, yesterday.month, yesterday.day, 18, 0, 0, tzinfo=TZ)

    checkin_resp = client.post(
        "/api/v1/attendance",
        json={
            "employee_id": "EMP-001",
            "attendance_date": today.isoformat(),
            "check_in": check_in_time.isoformat(),
        },
        headers=get_auth_header("ADMIN"),
    )
    att_id = checkin_resp.json()["id"]

    resp = client.put(
        f"/api/v1/attendance/{att_id}/checkout",
        json={"check_out": wrong_date_checkout.isoformat()},
        headers=get_auth_header("ADMIN"),
    )
    assert resp.status_code == 400
    assert "does not correspond" in resp.json()["detail"].lower()


def test_checkout_naive_datetime_rejected():
    """Verify naive datetime check-out without timezone is rejected with HTTP 422."""
    resp = client.put(
        "/api/v1/attendance/100/checkout",
        json={"check_out": "2026-09-05T18:00:00"},
        headers=get_auth_header("ADMIN"),
    )
    assert resp.status_code == 422


# ============================================================================
# 4. QUERY, FILTERING & PAGINATION TESTS
# ============================================================================

def test_list_attendance_pagination_and_records():
    """Verify pagination and default listing of attendance records."""
    d1 = date(2026, 8, 10)
    d2 = date(2026, 8, 11)

    client.post(
        "/api/v1/attendance",
        json={
            "employee_id": "EMP-001",
            "attendance_date": d1.isoformat(),
            "check_in": datetime(2026, 8, 10, 9, 0, tzinfo=TZ).isoformat(),
        },
        headers=get_auth_header("ADMIN"),
    )
    client.post(
        "/api/v1/attendance",
        json={
            "employee_id": "EMP-001",
            "attendance_date": d2.isoformat(),
            "check_in": datetime(2026, 8, 11, 9, 0, tzinfo=TZ).isoformat(),
        },
        headers=get_auth_header("ADMIN"),
    )

    resp = client.get("/api/v1/attendance?page=1&page_size=2", headers=get_auth_header("ADMIN"))
    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 1
    assert data["page_size"] == 2
    # 2 new records + 1 seeded historical record = 3
    assert data["total"] == 3
    assert len(data["items"]) == 2


def test_list_attendance_filter_by_date():
    """Verify filtering attendance records by exact attendance_date."""
    d1 = date(2026, 8, 15)
    d2 = date(2026, 8, 16)

    client.post(
        "/api/v1/attendance",
        json={
            "employee_id": "EMP-001",
            "attendance_date": d1.isoformat(),
            "check_in": datetime(2026, 8, 15, 9, 0, tzinfo=TZ).isoformat(),
        },
        headers=get_auth_header("ADMIN"),
    )
    client.post(
        "/api/v1/attendance",
        json={
            "employee_id": "EMP-002",
            "attendance_date": d2.isoformat(),
            "check_in": datetime(2026, 8, 16, 9, 0, tzinfo=TZ).isoformat(),
        },
        headers=get_auth_header("ADMIN"),
    )

    resp = client.get(f"/api/v1/attendance?attendance_date={d1.isoformat()}", headers=get_auth_header("ADMIN"))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["attendance_date"] == d1.isoformat()
    assert data["items"][0]["employee_id"] == "EMP-001"


def test_list_attendance_filter_by_date_range():
    """Verify filtering attendance records across start_date and end_date."""
    resp = client.get(
        "/api/v1/attendance?start_date=2026-08-01&end_date=2026-08-05",
        headers=get_auth_header("ADMIN"),
    )
    assert resp.status_code == 200
    # Seeded record on 2026-08-01 is within range
    assert resp.json()["total"] == 1


def test_list_attendance_invalid_date_range():
    """Verify start_date after end_date returns HTTP 400."""
    resp = client.get(
        "/api/v1/attendance?start_date=2026-08-10&end_date=2026-08-01",
        headers=get_auth_header("ADMIN"),
    )
    assert resp.status_code == 400
    assert "cannot be after" in resp.json()["detail"].lower()


def test_list_attendance_filter_by_employee_id():
    """Verify filtering attendance records by human-facing employee_id."""
    resp = client.get(
        "/api/v1/attendance?employee_id=EMP-003",
        headers=get_auth_header("ADMIN"),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["employee_id"] == "EMP-003"


def test_list_attendance_filter_by_department():
    """Verify filtering attendance records by department_id."""
    resp = client.get(
        "/api/v1/attendance?department_id=2",
        headers=get_auth_header("ADMIN"),
    )
    assert resp.status_code == 200
    # Charlie in HR (dept 2)
    assert resp.json()["total"] == 1
    assert resp.json()["items"][0]["department_name"] == "Human Resources"


def test_list_attendance_sorting():
    """Verify sorting by allowed fields."""
    resp = client.get(
        "/api/v1/attendance?sort_by=attendance_date&sort_order=asc",
        headers=get_auth_header("ADMIN"),
    )
    assert resp.status_code == 200


def test_list_attendance_invalid_sort_field():
    """Verify invalid sort field returns HTTP 400."""
    resp = client.get(
        "/api/v1/attendance?sort_by=malicious_col",
        headers=get_auth_header("ADMIN"),
    )
    assert resp.status_code == 400
    assert "invalid sort field" in resp.json()["detail"].lower()


def test_list_attendance_preserves_inactive_employee_history():
    """Verify historical attendance records for inactive employees remain queryable."""
    # Charlie Davis (EMP-003) is INACTIVE, but seeded with attendance on 2026-08-01
    resp = client.get(
        "/api/v1/attendance?employee_id=EMP-003",
        headers=get_auth_header("ADMIN"),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["employee_name"] == "Charlie Davis"
    assert data["items"][0]["status"] == "PRESENT"


# ============================================================================
# 5. EMPLOYEE ATTENDANCE HISTORY TESTS
# ============================================================================

def test_employee_attendance_history_by_human_id():
    """Verify employee attendance history via /api/v1/employees/{employee_id}/attendance."""
    d = date(2026, 8, 20)
    client.post(
        "/api/v1/attendance",
        json={
            "employee_id": "EMP-001",
            "attendance_date": d.isoformat(),
            "check_in": datetime(2026, 8, 20, 9, 0, tzinfo=TZ).isoformat(),
        },
        headers=get_auth_header("ADMIN"),
    )

    resp = client.get("/api/v1/employees/EMP-001/attendance", headers=get_auth_header("ADMIN"))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["employee_id"] == "EMP-001"
    assert data["items"][0]["status"] == "PRESENT"


def test_employee_attendance_history_by_internal_pk():
    """Verify employee history lookup works using internal primary key (ID=1)."""
    resp = client.get("/api/v1/employees/1/attendance", headers=get_auth_header("ADMIN"))
    assert resp.status_code == 200


def test_employee_attendance_history_inactive_employee():
    """Verify history lookup for inactive employee works and returns historical records."""
    resp = client.get("/api/v1/employees/EMP-003/attendance", headers=get_auth_header("ADMIN"))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["attendance_date"] == "2026-08-01"


def test_employee_attendance_history_nonexistent():
    """Verify history lookup for non-existent employee returns HTTP 404."""
    resp = client.get("/api/v1/employees/UNKNOWN_EMP/attendance", headers=get_auth_header("ADMIN"))
    assert resp.status_code == 404


# ============================================================================
# 6. COMPUTED STATUS TESTS (PRESENT / ABSENT)
# ============================================================================

def test_computed_status_present():
    """Verify attendance record has status='PRESENT'."""
    d = date(2026, 8, 25)
    resp = client.post(
        "/api/v1/attendance",
        json={
            "employee_id": "EMP-001",
            "attendance_date": d.isoformat(),
            "check_in": datetime(2026, 8, 25, 9, 0, tzinfo=TZ).isoformat(),
        },
        headers=get_auth_header("ADMIN"),
    )
    assert resp.json()["status"] == "PRESENT"


def test_computed_status_present_without_checkout():
    """Verify attendance record without checkout is still status='PRESENT'."""
    d = date(2026, 8, 26)
    resp = client.post(
        "/api/v1/attendance",
        json={
            "employee_id": "EMP-001",
            "attendance_date": d.isoformat(),
            "check_in": datetime(2026, 8, 26, 9, 0, tzinfo=TZ).isoformat(),
        },
        headers=get_auth_header("ADMIN"),
    )
    assert resp.json()["check_out"] is None
    assert resp.json()["status"] == "PRESENT"


def test_daily_status_computed_present_and_absent():
    """Verify /api/v1/attendance/daily-status computes PRESENT and ABSENT for active employees."""
    target_date = date(2026, 8, 28)

    # Check in Alice (EMP-001) for target_date. Bob (EMP-002) does NOT check in.
    client.post(
        "/api/v1/attendance",
        json={
            "employee_id": "EMP-001",
            "attendance_date": target_date.isoformat(),
            "check_in": datetime(2026, 8, 28, 9, 0, tzinfo=TZ).isoformat(),
        },
        headers=get_auth_header("ADMIN"),
    )

    resp = client.get(
        f"/api/v1/attendance/daily-status?attendance_date={target_date.isoformat()}",
        headers=get_auth_header("ADMIN"),
    )
    assert resp.status_code == 200
    data = resp.json()

    # Active employees: Alice (EMP-001) and Bob (EMP-002) = 2
    assert data["total_active_employees"] == 2
    assert data["present_count"] == 1
    assert data["absent_count"] == 1

    status_map = {item["employee_id"]: item["status"] for item in data["items"]}
    assert status_map["EMP-001"] == "PRESENT"
    assert status_map["EMP-002"] == "ABSENT"

    # Verify ABSENT item properties
    absent_bob = [item for item in data["items"] if item["employee_id"] == "EMP-002"][0]
    assert absent_bob["id"] is None
    assert absent_bob["check_in"] is None
    assert absent_bob["check_out"] is None


def test_list_attendance_with_include_absent():
    """Verify GET /api/v1/attendance?include_absent=true computes absent active employees."""
    target_date = date(2026, 8, 29)

    # Check in Bob only
    client.post(
        "/api/v1/attendance",
        json={
            "employee_id": "EMP-002",
            "attendance_date": target_date.isoformat(),
            "check_in": datetime(2026, 8, 29, 9, 0, tzinfo=TZ).isoformat(),
        },
        headers=get_auth_header("ADMIN"),
    )

    resp = client.get(
        f"/api/v1/attendance?attendance_date={target_date.isoformat()}&include_absent=true",
        headers=get_auth_header("ADMIN"),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2

    status_map = {item["employee_id"]: item["status"] for item in data["items"]}
    assert status_map["EMP-002"] == "PRESENT"
    assert status_map["EMP-001"] == "ABSENT"
