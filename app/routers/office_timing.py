# app/routers/office_timing.py

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.config.dependencies import get_db
from app.schemas.office_timing import (
    OfficeTimingCreate,
    OfficeTimingUpdate,
    OfficeTimingResponse,
    OfficeTimingListResponse,
)
from app.services.office_timing import OfficeTimingService
from app.utils.auth import get_current_user, admin_required, client_admin_required


router = APIRouter(prefix="/office-timings", tags=["Office Timings"])


# ============================================
# PERMISSION FUNCTION
# ============================================

def admin_or_client_admin_required(current_user=Depends(get_current_user)):
    """
    Dependency to check if user is either Platform Admin or Client Admin.
    """
    role = current_user.get("role")
    
    if role not in ["ADMIN", "PLATFORM_ADMIN", "CLIENT_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Platform Admins and Client Admins can access this resource."
        )
    
    return current_user


# ============================================
# ROUTES
# ============================================

@router.post("/", response_model=OfficeTimingResponse)
def create_office_timing(
    payload: OfficeTimingCreate,
    db: Session = Depends(get_db),
    current_user=Depends(admin_or_client_admin_required),
):
    """
    Create a new office timing configuration.
    
    - Platform Admin: Must provide client_id
    - Client Admin: client_id is automatically set from token
    """
    return OfficeTimingService.create_office_timing(payload, db, current_user)


@router.get("/", response_model=OfficeTimingListResponse)
def get_office_timings(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user=Depends(admin_or_client_admin_required),
):
    """
    Get paginated list of office timings with permission filtering.
    """
    return OfficeTimingService.get_office_timings(
        db=db,
        current_user=current_user,
        page=page,
        size=size,
    )


@router.get("/{office_timing_id}", response_model=OfficeTimingResponse)
def get_office_timing(
    office_timing_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(admin_or_client_admin_required),
):
    """
    Get a single office timing by ID.
    """
    return OfficeTimingService.get_office_timing(office_timing_id, db, current_user)


@router.put("/{office_timing_id}", response_model=OfficeTimingResponse)
def update_office_timing(
    office_timing_id: str,
    payload: OfficeTimingUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(admin_or_client_admin_required),
):
    """
    Update an existing office timing configuration.
    """
    return OfficeTimingService.update_office_timing(office_timing_id, payload, db, current_user)


@router.delete("/{office_timing_id}")
def delete_office_timing(
    office_timing_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(admin_or_client_admin_required),
):
    """
    Soft delete an office timing configuration.
    """
    return OfficeTimingService.delete_office_timing(office_timing_id, db, current_user)