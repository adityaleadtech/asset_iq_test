from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.config.dependencies import get_db
from app.utils.auth import service_permission_required
from app.schemas.asset_categories import (
    AssetCategoryCreate,
    AssetCategoryUpdate,
    AssetCategoryResponse
)
from app.services.asset_categories import (
    create_asset_category,
    get_asset_categories,
    get_asset_category_by_id,
    update_asset_category,
    deactivate_asset_category
)

router = APIRouter(
    prefix="/asset-categories",
    tags=["Asset Categories"]
)


@router.post(
    "",
    response_model=AssetCategoryResponse,
    summary="Create Asset Category",
    description="Create a new asset category. ADMIN and CLIENT_ADMIN only."
)
def create_category(
    category_data: AssetCategoryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        service_permission_required("ASSET_MANAGEMENT", "create")
    )
):
    return create_asset_category(db, category_data, current_user)


@router.get(
    "",
    response_model=List[AssetCategoryResponse],
    summary="Fetch Asset Categories",
    description="Fetch all active categories. Used in Asset Creation dropdown."
)
def fetch_categories(
    db: Session = Depends(get_db),
    current_user=Depends(
        service_permission_required("ASSET_MANAGEMENT", "read")
    )
):
    return get_asset_categories(db, current_user)


@router.get(
    "/{category_id}",
    response_model=AssetCategoryResponse,
    summary="Get Asset Category by ID"
)
def fetch_category(
    category_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
        service_permission_required("ASSET_MANAGEMENT", "read")
    )
):
    return get_asset_category_by_id(db, category_id, current_user)


@router.patch(
    "/{category_id}",
    response_model=AssetCategoryResponse,
    summary="Update Asset Category"
)
def update_category(
    category_id: str,
    category_data: AssetCategoryUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        service_permission_required("ASSET_MANAGEMENT", "update")
    )
):
    return update_asset_category(db, category_id, category_data, current_user)


@router.delete(
    "/{category_id}",
    summary="Deactivate Asset Category",
    description="Soft delete an asset category."
)
def delete_category(
    category_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
        service_permission_required("ASSET_MANAGEMENT", "delete")
    )
):
    deactivate_asset_category(db, category_id, current_user)
    return {"message": "Category deactivated successfully"}