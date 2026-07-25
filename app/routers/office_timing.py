from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    Query,
    status,
)

from sqlalchemy.orm import Session

from app.config.dependencies import get_db
from app.utils.auth import get_current_user

from app.schemas.office_timing import (
    OfficeTimingCreate,
    OfficeTimingUpdate,
    OfficeTimingResponse,
    OfficeTimingListResponse,
)

from app.services.office_timing import OfficeTimingService


# ============================================================
# Router
# ============================================================

router = APIRouter(
    prefix="/office-timings",
    tags=["Office Timings"],
)


# ============================================================
# Admin APIs
# ============================================================

@router.post(
    "",
    response_model=OfficeTimingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Office Timing",
    description="Create a new office timing configuration for a location.",
)
def create_office_timing(
    payload: OfficeTimingCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Create a new office timing.
    
    **Admin Only** - Requires PLATFORM_ADMIN or CLIENT_ADMIN role.
    
    - One office timing per location
    - Check-in time must be before check-out time
    - Configurable grace period and half-day threshold
    - Client Admin can only create for their client
    - Platform Admin must specify client_id
    """
    return OfficeTimingService.create_office_timing(
        payload=payload,
        db=db,
        current_user=current_user,
    )


@router.get(
    "",
    response_model=OfficeTimingListResponse,
    summary="Get Office Timings",
    description="Get all office timings with pagination and filtering.",
)
def get_office_timings(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    location_id: Optional[str] = Query(None, description="Filter by location ID"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Get all office timings with pagination.
    
    **Admin Only** - Requires PLATFORM_ADMIN or CLIENT_ADMIN role.
    
    - Client Admin sees only their client's office timings
    - Platform Admin sees all office timings
    - Optional filter by location_id
    """
    return OfficeTimingService.get_office_timings(
        db=db,
        current_user=current_user,
        page=page,
        size=size,
        location_id=location_id,
    )


@router.get(
    "/{office_timing_id}",
    response_model=OfficeTimingResponse,
    summary="Get Office Timing",
    description="Get office timing by ID.",
)
def get_office_timing(
    office_timing_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Get office timing by ID.
    
    **Admin Only** - Requires PLATFORM_ADMIN or CLIENT_ADMIN role.
    
    - Client Admin can only view their client's office timings
    - Platform Admin can view any office timing
    """
    return OfficeTimingService.get_office_timing(
        office_timing_id=office_timing_id,
        db=db,
        current_user=current_user,
    )


@router.patch(
    "/{office_timing_id}",
    response_model=OfficeTimingResponse,
    summary="Update Office Timing",
    description="Update office timing details.",
)
def update_office_timing(
    office_timing_id: str,
    payload: OfficeTimingUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Update office timing.
    
    **Admin Only** - Requires PLATFORM_ADMIN or CLIENT_ADMIN role.
    
    - Partial updates supported (only send fields to update)
    - Can activate/deactivate timing
    - Can change location (validates no conflict)
    - Validates time constraints
    - Client Admin can only update their client's office timings
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
    summary="Delete Office Timing",
    description="Soft delete office timing.",
)
def delete_office_timing(
    office_timing_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Soft delete office timing.
    
    **Admin Only** - Requires PLATFORM_ADMIN or CLIENT_ADMIN role.
    
    - Sets is_active = False
    - Does not physically delete the record
    - Prevents deletion if attendance records exist
    - Client Admin can only delete their client's office timings
    """
    return OfficeTimingService.delete_office_timing(
        office_timing_id=office_timing_id,
        db=db,
        current_user=current_user,
    )


# ============================================================
# Additional Admin APIs (Optional)
# ============================================================

@router.get(
    "/by-location/{location_id}",
    response_model=OfficeTimingResponse,
    summary="Get Office Timing by Location",
    description="Get active office timing for a specific location.",
)
def get_office_timing_by_location(
    location_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Get active office timing for a specific location.
    
    **Admin Only** - Requires PLATFORM_ADMIN or CLIENT_ADMIN role.
    
    - Returns the active office timing for the location
    - Useful for checking if a location has timing configured
    """
    # Query for active office timing for this location
    from app.models.office_timing import OfficeTiming
    from app.models.location import Location
    
    # Verify location exists and user has access
    location = (
        db.query(Location)
        .filter(Location.id == location_id)
        .first()
    )
    
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found."
        )
    
    # Permission check
    role = current_user.get("role")
    if role == "CLIENT_ADMIN" and location.client_id != current_user.get("client_id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this location."
        )
    
    office_timing = (
        db.query(OfficeTiming)
        .filter(
            OfficeTiming.location_id == location_id,
            OfficeTiming.is_active == True,
        )
        .first()
    )
    
    if not office_timing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active office timing found for this location."
        )
    
    return OfficeTimingResponse(
        id=office_timing.id,
        client_id=office_timing.client_id,
        location_id=office_timing.location_id,
        location_name=location.name,
        name=office_timing.name,
        check_in_time=office_timing.check_in_time,
        check_out_time=office_timing.check_out_time,
        late_after_minutes=office_timing.late_after_minutes,
        half_day_after_minutes=office_timing.half_day_after_minutes,
        is_active=office_timing.is_active,
        created_at=office_timing.created_at,
        updated_at=office_timing.updated_at,
    )