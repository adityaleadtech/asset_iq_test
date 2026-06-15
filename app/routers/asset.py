from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.config.dependencies import get_db

from app.utils.auth import (
    client_admin_required,
    admin_required,
    service_permission_required
)

from app.schemas.assets import (
    AssetCreate,
    AssetResponse,
    AssetUpdate,
    AssetUpdate
)

from app.services.assets import (
    create_asset,
    deactivate_asset,
    get_asset_by_id,
    get_assets,
    update_asset,
    update_asset
)


router = APIRouter(
    prefix="/assets",
    tags=["Assets"]
)


@router.post(
    "",
    response_model=AssetResponse,
    summary="Create Asset",
    description="""
    Create a new asset.

    Access:
    - CLIENT_ADMIN only

    Validation:
    - Client must have an active subscription
    - Asset limit must not be exceeded
    - Category must belong to client
    - Type must belong to selected category
    - Department must belong to client
    - Assigned user must belong to client

    Status Logic:
    - Assigned User → ASSIGNED
    - No Assigned User → AVAILABLE
    """
)
def create_new_asset(
    asset_data: AssetCreate,
    db: Session = Depends(get_db),
   current_user=Depends(
    service_permission_required(
        "ASSET_MANAGEMENT",
        "create"
    )
)
):
    return create_asset(
        db,
        asset_data,
        current_user
    )


@router.get(
    "",
    response_model=list[AssetResponse],
    summary="Fetch All Assets",
    description="""
    Fetch all assets based on user role.
    
    Access:
    - ADMIN: Sees all assets across all clients
    - CLIENT_ADMIN: Sees only their client's assets
    """
)
def fetch_all_assets(
    db: Session = Depends(get_db),
   current_user=Depends(
    service_permission_required(
        "ASSET_MANAGEMENT",
        "read"
    )
)
):
    return get_assets(
        db,
        current_user
    )


@router.get(
    "/{asset_id}",
    response_model=AssetResponse,
    summary="Fetch Asset by ID",
    description="""
    Fetch a single asset by its ID.
    
    Access:
    - ADMIN: Can fetch any asset
    - CLIENT_ADMIN: Can only fetch assets belonging to their client
    """
)
def fetch_asset(
    asset_id: str,
    db: Session = Depends(get_db),
  current_user=Depends(
    service_permission_required(
        "ASSET_MANAGEMENT",
        "read"
    )
)
):
    return get_asset_by_id(
        db,
        asset_id,
        current_user
    )


@router.patch(
    "/{asset_id}",
    response_model=AssetResponse,
    summary="Update Asset"
)
def update_existing_asset(
    asset_id: str,
    asset_data: AssetUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        service_permission_required(
            "ASSET_MANAGEMENT",
            "update"
        )
    )
):

    return update_asset(
        db,
        asset_id,
        asset_data,
        current_user
    )



@router.delete(
    "/{asset_id}",
    summary="Deactivate Asset"
)
def delete_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
        service_permission_required(
            "ASSET_MANAGEMENT",
            "delete"
        )
    )
):

    deactivate_asset(
        db,
        asset_id,
        current_user
    )

    return {
        "message":
        "Asset deactivated successfully"
    }