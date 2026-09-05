from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_role
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import dashboard_service

# Operational dashboard is strictly restricted to ADMIN and HR roles
router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
    dependencies=[Depends(require_role("ADMIN", "HR"))],
)


@router.get(
    "",
    response_model=DashboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Get aggregated operational dashboard metrics",
    description=(
        "Retrieve core workforce metrics including total employees, "
        "active employees, employees present today (Asia/Kolkata), employees absent today, "
        "and department-wise employee distribution counts. Restricted to ADMIN and HR roles."
    ),
)
def get_dashboard(
    target_date: Optional[date] = Query(
        None,
        alias="date",
        description="Optional target date (YYYY-MM-DD) to calculate metrics for (defaults to today in Asia/Kolkata)",
    ),
    db: Session = Depends(get_db),
) -> DashboardResponse:
    """Return consolidated operational metrics for the organization."""
    return dashboard_service.get_dashboard_metrics(db, target_date=target_date)
