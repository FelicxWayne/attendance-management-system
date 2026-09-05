from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.dependencies import get_current_user, get_db
from app.core.security import create_access_token, hash_password
from app.db.database import Base
from app.db.models.department import Department
from app.db.models.employee import Employee, EmployeeStatus
from app.db.models.user import User, UserRole
from app.main import app
from app.schemas.employee import EmployeeCreate, EmployeeResponse, EmployeeUpdate

# Isolated in-memory SQLite engine for employee management tests
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

    # Seed users for RBAC testing
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

    # Seed sample employees
    emp1 = Employee(
        id=1,
        employee_id="EMP-001",
        name="Alice Johnson",
        email="alice.johnson@example.com",
        mobile="1234567890",
        department_id=1,
        designation="Lead Architect",
        status=EmployeeStatus.ACTIVE.value,
    )
    emp2 = Employee(
        id=2,
        employee_id="EMP-002",
        name="Bob Smith",
        email="bob.smith@example.com",
        mobile="9876543210",
        department_id=2,
        designation="HR Specialist",
        status=EmployeeStatus.ACTIVE.value,
    )
    emp3 = Employee(
        id=3,
        employee_id="EMP-003",
        name="Charlie Brown",
        email="charlie.brown@example.com",
        mobile=None,
        department_id=1,
        designation="Junior Developer",
        status=EmployeeStatus.INACTIVE.value,
    )
    db.add_all([emp1, emp2, emp3])
    db.commit()
    db.close()

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


# ============================================================================
# 1. CREATE EMPLOYEE TESTS
# ============================================================================

def test_create_employee_success():
    """Verify creating an employee returns HTTP 201 with default ACTIVE status and employee_id."""
    payload = {
        "employee_id": "EMP-004",
        "name": "Diana Prince",
        "email": "diana.prince@example.com",
        "mobile": "5551234567",
        "department_id": 1,
        "designation": "Security Analyst",
    }
    response = client.post(
        "/api/v1/employees",
        json=payload,
        headers=get_auth_header("ADMIN"),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["employee_id"] == "EMP-004"
    assert "employee_code" not in data
    assert data["name"] == "Diana Prince"
    assert data["email"] == "diana.prince@example.com"
    assert data["mobile"] == "5551234567"
    assert data["department_id"] == 1
    assert data["department_name"] == "Engineering"
    assert data["designation"] == "Security Analyst"
    assert data["status"] == "ACTIVE"
    assert "created_at" in data
    assert "updated_at" in data
    assert "password" not in data


def test_create_employee_by_hr_success():
    """Verify HR users possess necessary privileges to add employees."""
    payload = {
        "employee_id": "EMP-005",
        "name": "Evan Wright",
        "email": "evan.wright@example.com",
        "department_id": 2,
        "designation": "Recruiter",
    }
    response = client.post(
        "/api/v1/employees",
        json=payload,
        headers=get_auth_header("HR", user_id=2),
    )
    assert response.status_code == 201
    assert response.json()["employee_id"] == "EMP-005"
    assert response.json()["department_name"] == "Human Resources"


def test_create_employee_duplicate_id():
    """Verify adding employee with duplicate employee_id returns HTTP 409."""
    payload = {
        "employee_id": "EMP-001",  # already seeded
        "name": "Duplicate Alice",
        "email": "different.alice@example.com",
        "department_id": 1,
        "designation": "Staff Engineer",
    }
    response = client.post(
        "/api/v1/employees",
        json=payload,
        headers=get_auth_header("ADMIN"),
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_create_employee_duplicate_email_case_insensitive():
    """Verify adding employee with duplicate email (different casing) returns HTTP 409."""
    payload = {
        "employee_id": "EMP-099",
        "name": "Different Name",
        "email": "ALICE.JOHNSON@example.com",  # matches alice.johnson@example.com
        "department_id": 1,
        "designation": "DevOps Engineer",
    }
    response = client.post(
        "/api/v1/employees",
        json=payload,
        headers=get_auth_header("ADMIN"),
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_create_employee_nonexistent_department():
    """Verify adding employee referencing non-existent department returns HTTP 404."""
    payload = {
        "employee_id": "EMP-010",
        "name": "Frank Castle",
        "email": "frank.castle@example.com",
        "department_id": 9999,  # does not exist
        "designation": "Strategist",
    }
    response = client.post(
        "/api/v1/employees",
        json=payload,
        headers=get_auth_header("ADMIN"),
    )
    assert response.status_code == 404
    assert "Department with ID 9999 not found" in response.json()["detail"]


def test_create_employee_validation_errors():
    """Verify Pydantic validation rejects invalid payloads with HTTP 422."""
    # Missing required name and invalid email format
    payload = {
        "employee_id": "EMP-011",
        "email": "not-an-email",
        "department_id": 1,
        "designation": "Tester",
    }
    response = client.post(
        "/api/v1/employees",
        json=payload,
        headers=get_auth_header("ADMIN"),
    )
    assert response.status_code == 422


def test_create_employee_unauthenticated():
    """Verify unauthenticated create request returns HTTP 401."""
    payload = {
        "employee_id": "EMP-012",
        "name": "Ghost User",
        "email": "ghost@example.com",
        "department_id": 1,
        "designation": "Tester",
    }
    response = client.post("/api/v1/employees", json=payload)
    assert response.status_code == 401


def test_create_employee_unauthorized_role():
    """Verify user with non-ADMIN/non-HR role returns HTTP 403."""
    unauthorized_user = User(id=99, username="guest_user", role="GUEST")
    app.dependency_overrides[get_current_user] = lambda: unauthorized_user
    try:
        payload = {
            "employee_id": "EMP-013",
            "name": "Guest User",
            "email": "guest@example.com",
            "department_id": 1,
            "designation": "Observer",
        }
        response = client.post(
            "/api/v1/employees",
            json=payload,
            headers={"Authorization": "Bearer mock_token"},
        )
        assert response.status_code == 403
        assert "Operation not permitted for current role" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)


# ============================================================================
# 2. LIST EMPLOYEES TESTS (Pagination, Search, Filter, Sort)
# ============================================================================

def test_list_employees_default():
    """Verify default listing returns all seeded items with metadata."""
    response = client.get("/api/v1/employees", headers=get_auth_header("ADMIN"))
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert data["total_pages"] == 1
    for item in data["items"]:
        assert "employee_id" in item
        assert "employee_code" not in item


def test_list_employees_pagination():
    """Verify pagination respects page and page_size limits."""
    response = client.get(
        "/api/v1/employees?page=1&page_size=2",
        headers=get_auth_header("ADMIN"),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total_pages"] == 2

    # Page 2
    response_p2 = client.get(
        "/api/v1/employees?page=2&page_size=2",
        headers=get_auth_header("ADMIN"),
    )
    assert response_p2.status_code == 200
    data_p2 = response_p2.json()
    assert len(data_p2["items"]) == 1


def test_list_employees_search_by_name():
    """Verify case-insensitive search by employee name."""
    response = client.get(
        "/api/v1/employees?search=alice",
        headers=get_auth_header("ADMIN"),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Alice Johnson"


def test_list_employees_search_by_employee_id():
    """Verify search by employee_id."""
    response = client.get(
        "/api/v1/employees?search=EMP-002",
        headers=get_auth_header("ADMIN"),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Bob Smith"
    assert data["items"][0]["employee_id"] == "EMP-002"


def test_list_employees_search_by_email():
    """Verify search by employee email."""
    response = client.get(
        "/api/v1/employees?search=charlie.brown",
        headers=get_auth_header("ADMIN"),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["email"] == "charlie.brown@example.com"


def test_list_employees_filter_by_status():
    """Verify filtering by ACTIVE and INACTIVE status."""
    resp_active = client.get(
        "/api/v1/employees?status=ACTIVE",
        headers=get_auth_header("ADMIN"),
    )
    assert resp_active.status_code == 200
    assert resp_active.json()["total"] == 2
    for item in resp_active.json()["items"]:
        assert item["status"] == "ACTIVE"

    resp_inactive = client.get(
        "/api/v1/employees?status=INACTIVE",
        headers=get_auth_header("ADMIN"),
    )
    assert resp_inactive.status_code == 200
    assert resp_inactive.json()["total"] == 1
    assert resp_inactive.json()["items"][0]["employee_id"] == "EMP-003"


def test_list_employees_filter_by_department():
    """Verify filtering by department_id."""
    resp = client.get(
        "/api/v1/employees?department_id=2",
        headers=get_auth_header("ADMIN"),
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 1
    assert resp.json()["items"][0]["department_name"] == "Human Resources"


def test_list_employees_sorting():
    """Verify safe whitelisted sorting by employee_id, name, and created_at."""
    # Sort by employee_id asc
    resp_asc = client.get(
        "/api/v1/employees?sort_by=employee_id&sort_order=asc",
        headers=get_auth_header("ADMIN"),
    )
    assert resp_asc.status_code == 200
    ids_asc = [item["employee_id"] for item in resp_asc.json()["items"]]
    assert ids_asc == ["EMP-001", "EMP-002", "EMP-003"]

    # Sort by name desc
    resp_desc = client.get(
        "/api/v1/employees?sort_by=name&sort_order=desc",
        headers=get_auth_header("ADMIN"),
    )
    assert resp_desc.status_code == 200
    names_desc = [item["name"] for item in resp_desc.json()["items"]]
    assert names_desc == sorted(names_desc, reverse=True)


def test_list_employees_invalid_sort_field():
    """Verify arbitrary / invalid sort field returns HTTP 400."""
    response = client.get(
        "/api/v1/employees?sort_by=malicious_column",
        headers=get_auth_header("ADMIN"),
    )
    assert response.status_code == 400
    assert "Invalid sort field" in response.json()["detail"]


def test_list_employees_empty_search():
    """Verify query matching no records cleanly returns 0 total and empty list."""
    response = client.get(
        "/api/v1/employees?search=NonExistentMatch12345",
        headers=get_auth_header("ADMIN"),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []
    assert data["total_pages"] == 0


# ============================================================================
# 3. GET EMPLOYEE DETAILS TESTS
# ============================================================================

def test_get_employee_details_success():
    """Verify retrieving existing employee details includes department information and employee_id."""
    response = client.get("/api/v1/employees/1", headers=get_auth_header("ADMIN"))
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["employee_id"] == "EMP-001"
    assert "employee_code" not in data
    assert data["name"] == "Alice Johnson"
    assert data["department_name"] == "Engineering"
    assert data["department"]["name"] == "Engineering"
    assert "password" not in data


def test_get_employee_details_nonexistent():
    """Verify retrieving nonexistent employee returns HTTP 404."""
    response = client.get("/api/v1/employees/999", headers=get_auth_header("ADMIN"))
    assert response.status_code == 404
    assert "Employee with ID 999 not found" in response.json()["detail"]


def test_get_employee_details_unauthenticated():
    """Verify retrieving employee without token returns HTTP 401."""
    response = client.get("/api/v1/employees/1")
    assert response.status_code == 401


# ============================================================================
# 4. UPDATE EMPLOYEE TESTS
# ============================================================================

def test_update_employee_success():
    """Verify updating employee fields succeeds and preserves timestamps and id."""
    payload = {
        "employee_id": "EMP-001-RENAMED",
        "name": "Alice J. Smith",
        "email": "alice.updated@example.com",
        "mobile": "1112223333",
        "department_id": 2,
        "designation": "Principal Engineer",
        "status": "ACTIVE",
    }
    response = client.put(
        "/api/v1/employees/1",
        json=payload,
        headers=get_auth_header("ADMIN"),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["employee_id"] == "EMP-001-RENAMED"
    assert "employee_code" not in data
    assert data["name"] == "Alice J. Smith"
    assert data["email"] == "alice.updated@example.com"
    assert data["department_id"] == 2
    assert data["department_name"] == "Human Resources"
    assert data["designation"] == "Principal Engineer"


def test_update_employee_keep_own_id_and_email():
    """Verify updating an employee while keeping own existing employee_id/email succeeds without 409."""
    payload = {
        "employee_id": "EMP-001",  # keeping own id
        "name": "Alice Johnson",
        "email": "alice.johnson@example.com",  # keeping own email
        "mobile": "1234567890",
        "department_id": 1,
        "designation": "Promoted Architect",
        "status": "ACTIVE",
    }
    response = client.put(
        "/api/v1/employees/1",
        json=payload,
        headers=get_auth_header("ADMIN"),
    )
    assert response.status_code == 200
    assert response.json()["employee_id"] == "EMP-001"
    assert response.json()["designation"] == "Promoted Architect"


def test_update_employee_duplicate_id():
    """Verify updating employee_id to conflict with another employee returns HTTP 409."""
    payload = {
        "employee_id": "EMP-002",  # belongs to Bob Smith (id=2)
        "name": "Alice Johnson",
        "email": "alice.unique@example.com",
        "department_id": 1,
        "designation": "Architect",
        "status": "ACTIVE",
    }
    response = client.put(
        "/api/v1/employees/1",
        json=payload,
        headers=get_auth_header("ADMIN"),
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_update_employee_duplicate_email():
    """Verify updating employee email to conflict with another employee returns HTTP 409."""
    payload = {
        "employee_id": "EMP-001",
        "name": "Alice Johnson",
        "email": "BOB.SMITH@example.com",  # case-insensitive match with Bob (id=2)
        "department_id": 1,
        "designation": "Architect",
        "status": "ACTIVE",
    }
    response = client.put(
        "/api/v1/employees/1",
        json=payload,
        headers=get_auth_header("ADMIN"),
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_update_employee_nonexistent_department():
    """Verify updating employee with nonexistent department returns HTTP 404."""
    payload = {
        "employee_id": "EMP-001",
        "name": "Alice Johnson",
        "email": "alice.johnson@example.com",
        "department_id": 8888,
        "designation": "Architect",
        "status": "ACTIVE",
    }
    response = client.put(
        "/api/v1/employees/1",
        json=payload,
        headers=get_auth_header("ADMIN"),
    )
    assert response.status_code == 404
    assert "Department with ID 8888 not found" in response.json()["detail"]


def test_update_employee_nonexistent():
    """Verify updating nonexistent employee returns HTTP 404."""
    payload = {
        "employee_id": "EMP-999",
        "name": "Ghost",
        "email": "ghost@example.com",
        "department_id": 1,
        "designation": "Ghost",
        "status": "ACTIVE",
    }
    response = client.put(
        "/api/v1/employees/999",
        json=payload,
        headers=get_auth_header("ADMIN"),
    )
    assert response.status_code == 404
    assert "Employee with ID 999 not found" in response.json()["detail"]


# ============================================================================
# 5. DELETE / DEACTIVATE EMPLOYEE TESTS
# ============================================================================

def test_deactivate_employee_soft_delete():
    """Verify DELETE /api/v1/employees/{id} marks status as INACTIVE without deleting row."""
    # Ensure employee is active before deactivation
    pre_resp = client.get("/api/v1/employees/1", headers=get_auth_header("ADMIN"))
    assert pre_resp.json()["status"] == "ACTIVE"

    # Send DELETE request
    del_resp = client.delete("/api/v1/employees/1", headers=get_auth_header("ADMIN"))
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "INACTIVE"
    assert del_resp.json()["id"] == 1
    assert del_resp.json()["employee_id"] == "EMP-001"

    # Verify directly against database that row is NOT deleted
    db = TestingSessionLocal()
    emp_in_db = db.query(Employee).filter(Employee.id == 1).first()
    assert emp_in_db is not None
    assert emp_in_db.status == "INACTIVE"
    assert emp_in_db.employee_id == "EMP-001"
    db.close()


def test_deactivate_employee_already_inactive_idempotent():
    """Verify deactivating an already INACTIVE employee operates safely and idempotently."""
    # EMP-003 is seeded with INACTIVE status
    del_resp = client.delete("/api/v1/employees/3", headers=get_auth_header("ADMIN"))
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "INACTIVE"


def test_deactivate_employee_nonexistent():
    """Verify deactivating nonexistent employee returns HTTP 404."""
    del_resp = client.delete("/api/v1/employees/999", headers=get_auth_header("ADMIN"))
    assert del_resp.status_code == 404
    assert "Employee with ID 999 not found" in del_resp.json()["detail"]


def test_inactive_employee_business_rule_contract():
    """Verify architectural requirement: inactive employee status is preserved for attendance restriction.

    Step 5 Attendance will enforce: An INACTIVE employee must not be allowed to receive NEW attendance records.
    """
    db = TestingSessionLocal()
    inactive_emp = db.query(Employee).filter(Employee.status == EmployeeStatus.INACTIVE.value).first()
    assert inactive_emp is not None
    assert inactive_emp.status == "INACTIVE"
    db.close()


# ============================================================================
# 6. VERIFY ZERO employee_code REFERENCES
# ============================================================================

def test_no_employee_code_references_in_model_or_schemas():
    """Verify that employee_code is completely removed from models, schemas, and responses."""
    # Model attributes
    assert not hasattr(Employee, "employee_code")
    assert hasattr(Employee, "employee_id")

    # Schema fields
    assert "employee_code" not in EmployeeCreate.model_fields
    assert "employee_id" in EmployeeCreate.model_fields

    assert "employee_code" not in EmployeeUpdate.model_fields
    assert "employee_id" in EmployeeUpdate.model_fields

    assert "employee_code" not in EmployeeResponse.model_fields
    assert "employee_id" in EmployeeResponse.model_fields

    # Response check from live API
    resp = client.get("/api/v1/employees/1", headers=get_auth_header("ADMIN"))
    assert resp.status_code == 200
    data = resp.json()
    assert "employee_code" not in data
    assert "employee_id" in data
