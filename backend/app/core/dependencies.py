from typing import Generator, List
from sqlalchemy.orm import Session

from app.db.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Provide a transactional database session per request.

    Ensures the session is cleanly closed after request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Future authentication and authorization dependencies
# Note: Implemented as architectural placeholders to maintain simplicity and avoid fake RBAC logic.

def get_current_user():
    """Dependency placeholder for retrieving the authenticated user from JWT token."""
    raise NotImplementedError("Authentication dependency will be implemented with user entities.")


def require_role(allowed_roles: List[str]):
    """Dependency factory placeholder for role-based authorization checks."""
    def role_checker():
        raise NotImplementedError("Role enforcement will be implemented with user entities.")
    return role_checker
