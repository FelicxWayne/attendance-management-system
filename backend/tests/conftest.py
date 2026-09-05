import os

# Provide test environment configuration before application modules are loaded
os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test-secret-key-for-pytest-environment-min-32-chars",
)
os.environ.setdefault("ENVIRONMENT", "testing")

from sqlalchemy import BigInteger
from sqlalchemy.ext.compiler import compiles


@compiles(BigInteger, "sqlite")
def compile_bigint_sqlite(element, compiler, **kw):
    """Compile BigInteger to INTEGER under SQLite to allow ROWID autoincrement primary keys."""
    return "INTEGER"

