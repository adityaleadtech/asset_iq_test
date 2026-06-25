from fastapi import (
    APIRouter,
    Depends,
    status,
    Query
)
from sqlalchemy.orm import Session
from typing import Optional, List

from app.config.dependencies import get_db
from app.enums.location_type import LocationType
from app.utils.auth import client_admin_required

from app.schemas.location import (
    LocationCreate,
    LocationCreateResponse,
    LocationDropdownResponse,
    LocationResponse,
    LocationUpdate,
    AssignableLocationResponse
)

from app.services.location import (
    create_location,
    get_locations_dropdown,
    get_all_locations,
    get_location_by_id,
    update_location,
    delete_location,
    get_client_locations
)

router = APIRouter(
    prefix="/locations",
    tags=["Locations"]
)


# ============================================
# CREATE LOCATION HIERARCHY
# ============================================
@router.post(
    "",
    response_model=LocationCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Location Hierarchy"
)
def create_location_hierarchy(
    payload: LocationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(client_admin_required)
):
    return create_location(
        db=db,
        payload=payload,
        client_id=current_user["client_id"]
    )


# ============================================
# GET DROPDOWN LOCATIONS
# ============================================
@router.get(
    "/dropdown",
    response_model=List[LocationDropdownResponse],
    summary="Get Locations for Cascading Dropdown"
)
def get_dropdown(
    type: LocationType = Query(...),
    parent_location_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(client_admin_required)
):
    return get_locations_dropdown(
        db=db,
        client_id=current_user["client_id"],
        location_type=type,
        parent_location_id=parent_location_id
    )


# ============================================
# GET ALL LOCATIONS
# ============================================
@router.get(
    "",
    response_model=List[LocationResponse],
    summary="Get All Locations"
)
def get_locations(
    db: Session = Depends(get_db),
    current_user=Depends(client_admin_required)
):
    return get_all_locations(
        db=db,
        client_id=current_user["client_id"]
    )

@router.get(
    "/assignable",
    response_model=List[AssignableLocationResponse],
    summary="Get Assignable Locations",
    description="""
Returns all leaf-most active locations belonging
to the authenticated client.

Used for:
- Asset Creation
- Asset Update
- Department Creation
- Department Update

Each item contains:
- Leaf location id
- Human readable path
- Complete hierarchy path
"""
)
def get_assignable_locations(
    db: Session = Depends(get_db),
    current_user=Depends(client_admin_required)
):
    return get_client_locations(
        db=db,
        client_id=current_user["client_id"]
    )
# ============================================
# GET LOCATION BY ID
# ============================================
@router.get(
    "/{location_id}",
    response_model=LocationResponse,
    summary="Get Location By ID"
)
def get_location(
    location_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(client_admin_required)
):
    return get_location_by_id(
        db=db,
        location_id=location_id,
        client_id=current_user["client_id"]
    )


# ============================================
# UPDATE LOCATION
# ============================================
@router.patch(
    "/{location_id}",
    response_model=LocationResponse,
    summary="Update Location"
)
def update_location_by_id(
    location_id: str,
    payload: LocationUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(client_admin_required)
):
    return update_location(
        db=db,
        location_id=location_id,
        payload=payload,
        client_id=current_user["client_id"]
    )


# ============================================
# DELETE LOCATION
# ============================================
@router.delete(
    "/{location_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Location"
)
def delete_location_by_id(
    location_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(client_admin_required)
):
    return delete_location(
        db=db,
        location_id=location_id,
        client_id=current_user["client_id"]
    )


# ============================================
# GET ASSIGNABLE LOCATIONS
# ============================================
