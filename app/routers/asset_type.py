from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.dependencies import get_db
from app.utils.auth import client_admin_required, service_permission_required

from app.schemas.asset_type import (
    AssetTypeCreate,
    AssetTypeUpdate,
    AssetTypeResponse
)

from app.services.asset_type import (
    create_asset_type,
    get_asset_types,
    get_asset_type_by_id,
    get_asset_types_by_category,
    update_asset_type,
    deactivate_asset_type
)

router = APIRouter(
    prefix="/asset-types",
    tags=["Asset Types"]
)
@router.post(
    "",
    response_model=AssetTypeResponse,
    summary="Create Asset Type",
    description="""
    Create a new asset type.

    Access:
    - CLIENT_ADMIN only

    Example:
    Category: Laptop

    Types:
    - Dell Latitude
    - HP Elitebook
    """
)
def create_new_asset_type(
    type_data: AssetTypeCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
    service_permission_required(
        "ASSET_MANAGEMENT",
        "create"
    )

)
):

    return create_asset_type(
        db,
        type_data,
        current_user
    )
@router.get(
    "",
    response_model=list[AssetTypeResponse],
    summary="Fetch Asset Types",
    description="""
    Fetch all asset types
    for the current client.

    Access:
    - CLIENT_ADMIN only
    """
)
def fetch_asset_types(
    db: Session = Depends(get_db),
current_user=Depends(
    service_permission_required(
        "ASSET_MANAGEMENT",
        "read"
    )
)
):

    return get_asset_types(
        db,
        current_user
    )

@router.get(
    "/category/{category_id}",
    response_model=list[AssetTypeResponse],
    summary="Fetch Types By Category",
    description="""
    Fetch all asset types
    belonging to a category.

    Access:
    - CLIENT_ADMIN only

    Usage:
    Asset Form

    Category Selected
      ↓
    Call this endpoint
      ↓
    Populate Type dropdown
    """
)
def fetch_asset_types_by_category(
    category_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
    service_permission_required(
        "ASSET_MANAGEMENT",
        "read"
    )
)
):

    return get_asset_types_by_category(
        db,
        category_id,
        current_user
    )

@router.get(
    "/{type_id}",
    response_model=AssetTypeResponse,
    summary="Fetch Asset Type"
)
def fetch_asset_type(
    type_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
        service_permission_required(
            "ASSET_MANAGEMENT",
            "read"
        )
    )
):

    return get_asset_type_by_id(
        db,
        type_id,
        current_user
    )


@router.patch(
    "/{type_id}",
    response_model=AssetTypeResponse,
    summary="Update Asset Type"
)
def update_existing_asset_type(
    type_id: str,
    type_data: AssetTypeUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        service_permission_required(
            "ASSET_MANAGEMENT",
            "update"
        )
    )
):

    return update_asset_type(
        db,
        type_id,
        type_data,
        current_user
    )


@router.delete(
    "/{type_id}",
    summary="Deactivate Asset Type"
)
def delete_asset_type(
    type_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
        service_permission_required(
            "ASSET_MANAGEMENT",
            "delete"
        )
    )
    ):

    deactivate_asset_type(
        db,
        type_id,
        current_user
    )

    return {
        "message":
        "Asset type deactivated successfully"
    }