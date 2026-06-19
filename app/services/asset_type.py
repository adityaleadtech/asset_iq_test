import uuid
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.asset_type import AssetType
from app.models.asset_categories import AssetCategory
from app.models.asset import Asset  # ✅ Fixed import
from app.schemas.asset_type import AssetTypeCreate, AssetTypeUpdate


def create_asset_type(
    db: Session,
    type_data: AssetTypeCreate,
    current_user: dict
) -> AssetType:
    """
    Create a new asset type.
    - ADMIN: Global types (client_id = None)
    - CLIENT_ADMIN: Client-specific types
    """
    # Determine client_id
    client_id = None if current_user["role"] == "ADMIN" else current_user["client_id"]

    # Validate category exists and belongs to same client/global
    category = (
        db.query(AssetCategory)
        .filter(
            AssetCategory.id == type_data.category_id,
            AssetCategory.is_active == True
        )
        .first()
    )

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Asset category not found"
        )

    # Check if category belongs to the same client scope
    if current_user["role"] != "ADMIN":
        if category.client_id is not None and category.client_id != current_user["client_id"]:
            raise HTTPException(
                status_code=403,
                detail="Category does not belong to your client"
            )

    # Check duplicate name (case-insensitive)
    existing = (
        db.query(AssetType)
        .filter(
            AssetType.name.ilike(type_data.name),  # ✅ Case-insensitive
            AssetType.client_id == client_id,
            AssetType.is_active == True
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Asset type with this name already exists"
        )

    asset_type = AssetType(
        id=str(uuid.uuid4()),
        client_id=client_id,
        category_id=type_data.category_id,
        name=type_data.name,
        description=type_data.description,
        created_by=current_user["id"],
        is_active=True
    )

    try:
        db.add(asset_type)
        db.commit()
        db.refresh(asset_type)
        return asset_type
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create asset type: {str(e)}"
        )


from fastapi import HTTPException


def get_asset_types_by_category(
    db: Session,
    category_id: str,
    current_user: dict
):
    category = (
        db.query(AssetCategory)
        .filter(
            AssetCategory.id == category_id,
            AssetCategory.is_active == True
        )
        .first()
    )

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Asset category not found"
        )

    query = (
        db.query(AssetType)
        .filter(
            AssetType.category_id == category_id,
            AssetType.is_active == True
        )
    )

    # Platform Admin
    if current_user["role"] == "ADMIN":
        return query.all()

    # Client Admin / Manager
    return (
        query.filter(
            or_(
                AssetType.client_id == current_user["client_id"],
                AssetType.client_id.is_(None)
            )
        )
        .all()
    )

def get_asset_types(
    db: Session,
    current_user: dict
) -> List[AssetType]:
    """
    Get all active asset types with proper scope.
    - ADMIN: Sees ALL types (global + all clients)
    - CLIENT_ADMIN: Sees their types + global types
    """
    if current_user["role"] == "ADMIN":
        # ✅ ADMIN sees ALL types
        return (
            db.query(AssetType)
            .filter(
                AssetType.is_active == True
            )
            .all()
        )

    # ✅ CLIENT_ADMIN sees their types + global types
    return (
        db.query(AssetType)
        .filter(
            AssetType.is_active == True,
            or_(  # ✅ Fixed OR condition
                AssetType.client_id == current_user["client_id"],
                AssetType.client_id.is_(None)
            )
        )
        .all()
    )


def get_asset_type_by_id(
    db: Session,
    type_id: str,
    current_user: dict
) -> AssetType:
    """
    Get a single asset type by ID with access control.
    """
    asset_type = (
        db.query(AssetType)
        .filter(
            AssetType.id == type_id,
            AssetType.is_active == True
        )
        .first()
    )

    if not asset_type:
        raise HTTPException(
            status_code=404,
            detail="Asset type not found"
        )

    if current_user["role"] == "ADMIN":
        return asset_type

    if (
        asset_type.client_id is not None
        and asset_type.client_id != current_user["client_id"]
    ):
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    return asset_type


def update_asset_type(
    db: Session,
    type_id: str,
    type_data: AssetTypeUpdate,
    current_user: dict
) -> AssetType:
    """
    Update an existing asset type.
    """
    asset_type = get_asset_type_by_id(db, type_id, current_user)

    # ✅ Prevent CLIENT_ADMIN from updating global types
    if (
        asset_type.client_id is None
        and current_user["role"] != "ADMIN"
    ):
        raise HTTPException(
            status_code=403,
            detail="Only platform admin can update global asset types"
        )

    update_data = type_data.model_dump(exclude_unset=True)

    # Validate category if being updated
    if "category_id" in update_data:
        category = (
            db.query(AssetCategory)
            .filter(
                AssetCategory.id == update_data["category_id"],
                AssetCategory.is_active == True
            )
            .first()
        )

        if not category:
            raise HTTPException(
                status_code=404,
                detail="Asset category not found"
            )

        if current_user["role"] != "ADMIN":
            if category.client_id is not None and category.client_id != current_user["client_id"]:
                raise HTTPException(
                    status_code=403,
                    detail="Category does not belong to your client"
                )

    # Check duplicate name (case-insensitive)
    if "name" in update_data:
        existing = (
            db.query(AssetType)
            .filter(
                AssetType.name.ilike(update_data["name"]),  # ✅ Case-insensitive
                AssetType.client_id == asset_type.client_id,
                AssetType.id != type_id,
                AssetType.is_active == True
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=400,
                detail="Asset type with this name already exists"
            )

    try:
        for key, value in update_data.items():
            setattr(asset_type, key, value)

        db.commit()
        db.refresh(asset_type)
        return asset_type
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update asset type: {str(e)}"
        )


def deactivate_asset_type(
    db: Session,
    type_id: str,
    current_user: dict
) -> AssetType:
    """
    Soft delete an asset type.
    """
    asset_type = get_asset_type_by_id(db, type_id, current_user)

    # ✅ Prevent CLIENT_ADMIN from deleting global types
    if (
        asset_type.client_id is None
        and current_user["role"] != "ADMIN"
    ):
        raise HTTPException(
            status_code=403,
            detail="Only platform admin can deactivate global asset types"
        )

    # Check if type is being used by any assets
    asset_count = (
        db.query(Asset)
        .filter(
            Asset.type_id == type_id,
            Asset.is_active == True
        )
        .count()
    )

    if asset_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot deactivate type. It is used by {asset_count} asset(s)"
        )

    try:
        asset_type.is_active = False
        db.commit()
        db.refresh(asset_type)
        return asset_type
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to deactivate asset type: {str(e)}"
        )