from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend REST API for Mini Attendance Management System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["General"])
def root():
    """Root endpoint welcoming clients to the API."""
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint to verify service operational status."""
    return {
        "status": "ok"
    }


# Future business endpoints will be registered under /api/v1
# e.g., app.include_router(api_v1_router, prefix="/api/v1")
