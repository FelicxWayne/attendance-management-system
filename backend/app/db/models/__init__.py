"""SQLAlchemy entity models registry.

All future database models will be imported here to enable Alembic autogenerate detection.
"""

from app.db.database import Base

__all__ = ["Base"]
