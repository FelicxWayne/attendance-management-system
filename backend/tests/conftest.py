import os

# Provide test environment configuration before application modules are loaded
os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test-secret-key-for-pytest-environment-min-32-chars",
)
os.environ.setdefault("ENVIRONMENT", "testing")
