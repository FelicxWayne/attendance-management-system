"""API route handlers and controllers."""

from app.routers.auth import router as auth_router
from app.routers.employees import router as employees_router

__all__ = [
    "auth_router",
    "employees_router",
]
