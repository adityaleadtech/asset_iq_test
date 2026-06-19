import uuid
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.asset_categories import AssetCategory
from app.models.asset import Asset  # ✅ Fixed import (plural)
from app.schemas.asset_categories import AssetCategoryCreate, AssetCategoryUpdate


def create_asset_category(
    db: Session,
    category_data: AssetCategoryCreate,
    current_user: dict
) -> AssetCategory:
    """
    Create a new asset category.
    - ADMIN: Can create global categories (client_id = None)
    - CLIENT_ADMIN: Can create client-specific categories
    """
    # Determine client_id
    client_id = None
    if current_user["role"] == "ADMIN":
        # ADMIN can create global categories
        client_id = None
    else:
        # CLIENT_ADMIN creates client-specific categories
        client_id = current_user["client_id"]

    # Check if category already exists (case-insensitive)
    existing = (
        db.query(AssetCategory)
        .filter(
            AssetCategory.name.ilike(category_data.name),  # ✅ Case-insensitive
            AssetCategory.client_id == client_id,
            AssetCategory.is_active == True
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Category with this name already exists"
        )

    category = AssetCategory(
        id=str(uuid.uuid4()),
        client_id=client_id,
        name=category_data.name,
        description=category_data.description,
        created_by=current_user["id"],
        is_active=True
    )

    try:
        db.add(category)
        db.commit()
        db.refresh(category)
        return category
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create asset category: {str(e)}"
        )


def get_asset_categories(
    db: Session,
    current_user: dict
) -> List[AssetCategory]:
    """
    Get all active asset categories with proper scope.
    - ADMIN: Sees ALL categories (global + all clients)
    - CLIENT_ADMIN: Sees their client-specific categories + global categories
    """
    if current_user["role"] == "ADMIN":
        # ✅ ADMIN sees ALL categories (global + client-specific)
        return (
            db.query(AssetCategory)
            .filter(
                AssetCategory.is_active == True
            )
            .all()
        )

    # ✅ CLIENT_ADMIN sees their categories + global categories
    return (
        db.query(AssetCategory)
        .filter(
            AssetCategory.is_active == True,
            or_(  # ✅ Fixed OR condition with proper import
                AssetCategory.client_id == current_user["client_id"],
                AssetCategory.client_id.is_(None)
            )
        )
        .all()
    )


def get_asset_category_by_id(
    db: Session,
    category_id: str,
    current_user: dict
) -> AssetCategory:
    """
    Get a single category by ID with access control.
    """
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

    # ✅ ADMIN can access any category
    if current_user["role"] == "ADMIN":
        return category

    # ✅ CLIENT_ADMIN can only access their categories or global categories
    if (
        category.client_id is not None
        and category.client_id != current_user["client_id"]
    ):
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    return category


def update_asset_category(
    db: Session,
    category_id: str,
    category_data: AssetCategoryUpdate,
    current_user: dict
) -> AssetCategory:
    """
    Update an existing category.
    """
    category = get_asset_category_by_id(db, category_id, current_user)

    # ✅ Prevent CLIENT_ADMIN from updating global categories
    if (
        category.client_id is None
        and current_user["role"] != "ADMIN"
    ):
        raise HTTPException(
            status_code=403,
            detail="Only platform admin can update global categories"
        )

    update_data = category_data.model_dump(exclude_unset=True)

    # Check for duplicate name if name is being changed (case-insensitive)
    if "name" in update_data:
        existing = (
            db.query(AssetCategory)
            .filter(
                AssetCategory.name.ilike(update_data["name"]),  # ✅ Case-insensitive
                AssetCategory.client_id == category.client_id,
                AssetCategory.id != category_id,
                AssetCategory.is_active == True
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=400,
                detail="Category with this name already exists"
            )

    try:
        for key, value in update_data.items():
            setattr(category, key, value)

        db.commit()
        db.refresh(category)
        return category
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update asset category: {str(e)}"
        )


def deactivate_asset_category(
    db: Session,
    category_id: str,
    current_user: dict
) -> AssetCategory:
    """
    Soft delete a category.
    """
    category = get_asset_category_by_id(db, category_id, current_user)

    # ✅ Prevent CLIENT_ADMIN from deleting global categories
    if (
        category.client_id is None
        and current_user["role"] != "ADMIN"
    ):
        raise HTTPException(
            status_code=403,
            detail="Only platform admin can deactivate global categories"
        )

    # Check if category is being used by any assets
    asset_count = (
        db.query(Asset)
        .filter(
            Asset.category_id == category_id,
            Asset.is_active == True
        )
        .count()
    )

    if asset_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot deactivate category. It is used by {asset_count} asset(s)"
        )

    try:
        category.is_active = False
        db.commit()
        db.refresh(category)
        return category
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to deactivate asset category: {str(e)}"
        )