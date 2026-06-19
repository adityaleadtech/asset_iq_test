from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.config.dependencies import get_db  # ✅ Correct path
from app.schemas.dashboard import ClientDashboardResponse, ManagerDashboardResponse, PlatformDashboardResponse
from app.services.dashboard import (  # ✅ Singular
    get_client_dashboard,
    get_admin_dashboard,
    get_manager_dashboard,
    get_platform_dashboard
)
from app.utils.auth import admin_required, get_current_user

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get(
    "/platform",
    response_model=PlatformDashboardResponse,
    summary="Platform Dashboard"
)
def fetch_platform_dashboard(
    db: Session = Depends(get_db),
    current_admin=Depends(admin_required)
):
    return get_platform_dashboard(
        db,
        current_admin
    )

@router.get("/client", response_model=ClientDashboardResponse)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    client_id: Optional[str] = Query(
        None,
        description="Required for ADMIN users"
    )
):
    """
    Get client dashboard data.
    
    - **ADMIN**: Can view any client's dashboard by providing client_id
    - **Others**: Automatically view their own client's dashboard
    """
    result = get_client_dashboard(db, current_user, client_id)
    return result


@router.get("/admin", response_model=dict)
def get_admin_dashboard_endpoint(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get platform-wide admin dashboard (ADMIN only).
    """
    return get_admin_dashboard(db, current_user)



@router.get(
    "/manager",
    response_model=ManagerDashboardResponse,
    summary="Manager Dashboard"
)
def fetch_manager_dashboard(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return get_manager_dashboard(
        db,
        current_user
    )