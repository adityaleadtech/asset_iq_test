from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.dependencies import get_db
from app.utils.auth import service_permission_required
from app.schemas.assets import (
    AssetCreate,
    AssetResponse,
    AssetUpdate
)

from app.schemas.assets import (
    AssetAssignRequest
)


from app.services.assets import (
    assign_asset,
    create_asset,
    deactivate_asset,
    get_asset_by_id,
    get_assets,
    unassign_asset,
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

    Required Permission:
    - ASSET_MANAGEMENT.create
    """
)
def create_new_asset(
    asset_data: AssetCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        service_permission_required("ASSET_MANAGEMENT", "create")
    )
):
    return create_asset(db, asset_data, current_user)

@router.get(
    "",
    response_model=list[AssetResponse],
    summary="Fetch Assets",
    description="""
    Fetch assets visible to the current user.

    Role-Based Visibility:

    **ADMIN**
    - Can view all assets across all clients

    **CLIENT_ADMIN**
    - Can view all assets belonging to their client

    **MANAGER**
    - Can view assets belonging to departments they manage
    - If a manager manages multiple departments, they see all of them

    **USER**
    - Can view only assets assigned to them

    Required Permission:
    - ASSET_MANAGEMENT.read
    """
)
def fetch_all_assets(
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        service_permission_required("ASSET_MANAGEMENT", "read")
    )
):
    return get_assets(db, current_user)

@router.get(
    "/{asset_id}",
    response_model=AssetResponse,
    summary="Fetch Asset by ID",
    description="""
    Fetch a single asset by its ID.

    Role-Based Access:

    **ADMIN**
    - Can fetch any asset

    **CLIENT_ADMIN**
    - Can only fetch assets belonging to their client

    **MANAGER**
    - Can only fetch assets belonging to departments they manage
    - If a manager manages multiple departments, they can access assets from any of them

    **USER**
    - Can only fetch assets assigned to them

    Required Permission:
    - ASSET_MANAGEMENT.read
    """
)
def fetch_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        service_permission_required("ASSET_MANAGEMENT", "read")
    )
):
    return get_asset_by_id(db, asset_id, current_user)

@router.patch(
    "/{asset_id}",
    response_model=AssetResponse,
    summary="Update Asset",
    description="""
    Update an existing asset.

    Access:
    - CLIENT_ADMIN only

    Validation on Update:
    - If category is updated, it must belong to client
    - If type is updated, it must belong to client and selected category
    - If department is updated, it must belong to client
    - If assigned user is updated, they must belong to client

    Required Permission:
    - ASSET_MANAGEMENT.update
    """
)
def update_existing_asset(
    asset_id: str,
    asset_data: AssetUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        service_permission_required("ASSET_MANAGEMENT", "update")
    )
):
    return update_asset(db, asset_id, asset_data, current_user)

@router.delete(
    "/{asset_id}",
    summary="Deactivate Asset",
    description="""
    Deactivate an asset.

    Access:
    - CLIENT_ADMIN only

    Required Permission:
    - ASSET_MANAGEMENT.delete
    """
)
def delete_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        service_permission_required("ASSET_MANAGEMENT", "delete")
    )
):
    deactivate_asset(db, asset_id, current_user)
    return {"message": "Asset deactivated successfully"}




@router.post(
    "/{asset_id}/assign",
    response_model=AssetResponse,
    summary="Assign Asset"
)
def assign_existing_asset(
    asset_id: str,
    request: AssetAssignRequest,
    db: Session = Depends(get_db),
    current_user=Depends(
        service_permission_required(
            "ASSET_MANAGEMENT",
            "update"
        )
    )
):
    return assign_asset(
        db,
        asset_id,
        request.user_id,
        current_user
    )


@router.post(
    "/{asset_id}/unassign",
    response_model=AssetResponse,
    summary="Unassign Asset",
    description="""
    Remove the current user assignment from an asset.

    Access:
    - ADMIN
    - CLIENT_ADMIN
    - MANAGER (if they have ASSET_MANAGEMENT.update permission)

    Behaviour:
    - Removes assigned user
    - Changes asset status to AVAILABLE
    - Asset remains in its department
    - Asset becomes available for reassignment

    Required Permission:
    - ASSET_MANAGEMENT.update
    """
)
def unassign_existing_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
        service_permission_required(
            "ASSET_MANAGEMENT",
            "update"
        )
    )
):
    return unassign_asset(
        db,
        asset_id,
        current_user
    )




from app.schemas.assets import (
    AssetAssignRequest
)

from app.services.assets import (
    assign_asset
)

@router.post(
    "/{asset_id}/assign",
    response_model=AssetResponse,
    summary="Assign Asset",
    description="""
    Assign an asset to a user.

    Access:
    - ADMIN
    - CLIENT_ADMIN
    - MANAGER

    Validation:
    - Asset must exist
    - User must exist
    - User must belong to same client
    - Managers can only assign assets
      within their department
    """
)
def assign_existing_asset(
    asset_id: str,
    request: AssetAssignRequest,
    db: Session = Depends(get_db),
    current_user=Depends(
        service_permission_required(
            "ASSET_MANAGEMENT",
            "update"
        )
    )
):
    return assign_asset(
        db,
        asset_id,
        request.user_id,
        current_user
    )


from app.services.assets import (
    assign_asset,
    unassign_asset
)

@router.post(
    "/{asset_id}/unassign",
    response_model=AssetResponse,
    summary="Unassign Asset",
    description="""
    Remove the current user assignment from an asset.

    Access:
    - ADMIN
    - CLIENT_ADMIN
    - MANAGER

    Validation:
    - Asset must exist
    - Asset must be assigned
    - Managers can only unassign assets
      from departments they manage

    Behaviour:
    - assigned_to_user_id = null
    - status = AVAILABLE
    """
)
def unassign_existing_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
        service_permission_required(
            "ASSET_MANAGEMENT",
            "update"
        )
    )
):
    return unassign_asset(
        db,
        asset_id,
        current_user
    )