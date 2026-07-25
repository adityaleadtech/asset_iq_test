# app/routers/office_timing.py

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.config.dependencies import get_db

from app.schemas.office_timing import (
    OfficeTimingCreate,
    OfficeTimingUpdate,
    OfficeTimingResponse,
    OfficeTimingListResponse,
)

from app.services.office_timing import OfficeTimingService

from app.utils.security import get_current_user


router = APIRouter(
    prefix="/office-timings",
    tags=["Office Timings"],
)


@router.post(
    "",
    response_model=OfficeTimingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new office timing configuration"
)
def create_office_timing(
    payload: OfficeTimingCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Create a new office timing configuration.
    
    - **Platform Admin**: Can create for any client (must provide client_id)
    - **Client Admin**: Can create only for their own client
    
    Required fields:
    - location_id: ID of the location
    - name: Name of the timing configuration
    - check_in_time: Expected check-in time
    - check_out_time: Expected check-out time
    
    Optional fields:
    - client_id: Required for Platform Admin
    - late_after_minutes: Minutes after check-in to mark as late (default: 15)
    - half_day_after_minutes: Minutes after check-in to mark as half-day (default: 240)
    """
    return OfficeTimingService.create_office_timing(
        payload=payload,
        db=db,
        current_user=current_user,
    )


@router.get(
    "",
    response_model=OfficeTimingListResponse,
    summary="Get paginated list of office timings"
)
def get_office_timings(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get a paginated list of office timing configurations.
    
    - **Platform Admin**: Can view all office timings across all clients
    - **Client Admin**: Can view only their client's office timings
    
    Results are paginated and ordered by creation date (newest first).
    """
    return OfficeTimingService.get_office_timings(
        db=db,
        current_user=current_user,
        page=page,
        size=size,
    )


@router.get(
    "/{office_timing_id}",
    response_model=OfficeTimingResponse,
    summary="Get a specific office timing by ID"
)
def get_office_timing(
    office_timing_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get a specific office timing configuration by its ID.
    
    - **Platform Admin**: Can view any office timing
    - **Client Admin**: Can view only their client's office timings
    
    Returns 404 if office timing not found or inactive.
    """
    return OfficeTimingService.get_office_timing(
        office_timing_id=office_timing_id,
        db=db,
        current_user=current_user,
    )


@router.patch(
    "/{office_timing_id}",
    response_model=OfficeTimingResponse,
    summary="Update an office timing configuration"
)
def update_office_timing(
    office_timing_id: str,
    payload: OfficeTimingUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Update an existing office timing configuration.
    
    All fields are optional. Only provided fields will be updated.
    
    - **Platform Admin**: Can update any office timing
    - **Client Admin**: Can update only their client's office timings
    
    Validations:
    - If location_id is changed, new location must exist and belong to same client
    - No duplicate active office timing for the same location
    - Check-out time must be greater than check-in time
    """
    return OfficeTimingService.update_office_timing(
        office_timing_id=office_timing_id,
        payload=payload,
        db=db,
        current_user=current_user,
    )


@router.delete(
    "/{office_timing_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete an office timing configuration"
)
def delete_office_timing(
    office_timing_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Soft delete an office timing configuration.
    
    This performs a soft delete by setting is_active to False.
    The record remains in the database but won't be returned in queries.
    
    - **Platform Admin**: Can delete any office timing
    - **Client Admin**: Can delete only their client's office timings
    
    Returns a success message upon deletion.
    """
    return OfficeTimingService.delete_office_timing(
        office_timing_id=office_timing_id,
        db=db,
        current_user=current_user,
    )