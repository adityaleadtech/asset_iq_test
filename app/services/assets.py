import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.subscription import Subscription
from app.models.asset_categories import AssetCategory
from app.models.asset_type import AssetType
from app.models.departments import Department
from app.models.users import User


def create_asset(
    db: Session,
    asset_data,
    current_user
):
    subscription = (
        db.query(Subscription)
        .filter(
            Subscription.client_id == current_user["client_id"],
            Subscription.status == "ACTIVE"
        )
        .first()
    )

    if not subscription:
        raise HTTPException(
            status_code=400,
            detail="No active subscription found"
        )

    asset_count = (
        db.query(Asset)
        .filter(
            Asset.client_id == current_user["client_id"],
            Asset.is_active == True
        )
        .count()
    )

    if asset_count >= subscription.max_assets:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Asset limit reached. "
                f"Maximum allowed: "
                f"{subscription.max_assets}"
            )
        )

    category = (
        db.query(AssetCategory)
        .filter(
            AssetCategory.id == asset_data.category_id,
            AssetCategory.client_id == current_user["client_id"],
            AssetCategory.is_active == True
        )
        .first()
    )

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Asset category not found"
        )

    asset_type = (
        db.query(AssetType)
        .filter(
            AssetType.id == asset_data.type_id,
            AssetType.client_id == current_user["client_id"],
            AssetType.is_active == True
        )
        .first()
    )

    if not asset_type:
        raise HTTPException(
            status_code=404,
            detail="Asset type not found"
        )

    if asset_type.category_id != category.id:
        raise HTTPException(
            status_code=400,
            detail=(
                "Asset type does not belong "
                "to selected category"
            )
        )

    department = (
        db.query(Department)
        .filter(
            Department.id == asset_data.department_id,
            Department.client_id == current_user["client_id"],
            Department.is_active == True
        )
        .first()
    )

    if not department:
        raise HTTPException(
            status_code=404,
            detail="Department not found"
        )

    assigned_user = None

    if asset_data.assigned_to_user_id:
        assigned_user = (
            db.query(User)
            .filter(
                User.id == asset_data.assigned_to_user_id,
                User.client_id == current_user["client_id"],
                User.is_active == True
            )
            .first()
        )

        if not assigned_user:
            raise HTTPException(
                status_code=404,
                detail="Assigned user not found"
            )

    status = "ASSIGNED" if assigned_user else "AVAILABLE"

    asset = Asset(
        id=str(uuid.uuid4()),
        client_id=current_user["client_id"],
        category_id=asset_data.category_id,
        type_id=asset_data.type_id,
        department_id=asset_data.department_id,
        assigned_to_user_id=asset_data.assigned_to_user_id,
        name=asset_data.name,
        description=asset_data.description,
        serial_number=asset_data.serial_number,
        model=asset_data.model,
        manufacturer=asset_data.manufacturer,
        purchase_date=asset_data.purchase_date,
        purchase_value=asset_data.purchase_value,
        status=status,
        created_by=current_user["id"],
        is_active=True
    )

    db.add(asset)
    db.commit()
    db.refresh(asset)

    return asset


def get_assets(db, current_user):
    if current_user["role"] == "ADMIN":
        return (
            db.query(Asset)
            .filter(Asset.is_active == True)
            .all()
        )

    return (
        db.query(Asset)
        .filter(
            Asset.client_id == current_user["client_id"],
            Asset.is_active == True
        )
        .all()
    )


def get_asset_by_id(db, asset_id: str, current_user):
    asset = (
        db.query(Asset)
        .filter(
            Asset.id == asset_id,
            Asset.is_active == True
        )
        .first()
    )

    # ✅ BUG 1 FIX: Check if asset exists FIRST
    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Asset not found"
        )

    # ✅ BUG 1 FIX: Check access AFTER confirming asset exists
    if current_user["role"] != "ADMIN":
        if asset.client_id != current_user["client_id"]:
            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )

    return asset


def update_asset(db, asset_id: str, asset_data, current_user):
    asset = get_asset_by_id(db, asset_id, current_user)

    update_data = asset_data.model_dump(exclude_unset=True)
    
    # ✅ BUG 2 FIX: Fix indentation for category validation
    if "category_id" in update_data:
        category = (
            db.query(AssetCategory)
            .filter(
                AssetCategory.id == update_data["category_id"],
                AssetCategory.client_id == current_user["client_id"],
                AssetCategory.is_active == True
            )
            .first()
        )

        if not category:
            raise HTTPException(
                status_code=404,
                detail="Asset category not found"
            )

    # ✅ BUG 3 FIX: Add type validation
    if "type_id" in update_data:
        asset_type = (
            db.query(AssetType)
            .filter(
                AssetType.id == update_data["type_id"],
                AssetType.client_id == current_user["client_id"],
                AssetType.is_active == True
            )
            .first()
        )

        if not asset_type:
            raise HTTPException(
                status_code=404,
                detail="Asset type not found"
            )

    # ✅ BUG 4 FIX: Add department validation
    if "department_id" in update_data:
        department = (
            db.query(Department)
            .filter(
                Department.id == update_data["department_id"],
                Department.client_id == current_user["client_id"],
                Department.is_active == True
            )
            .first()
        )

        if not department:
            raise HTTPException(
                status_code=404,
                detail="Department not found"
            )

    # ✅ BUG 5 FIX: Add assigned user validation
    if "assigned_to_user_id" in update_data:
        if update_data["assigned_to_user_id"]:
            assigned_user = (
                db.query(User)
                .filter(
                    User.id == update_data["assigned_to_user_id"],
                    User.client_id == current_user["client_id"],
                    User.is_active == True
                )
                .first()
            )

            if not assigned_user:
                raise HTTPException(
                    status_code=404,
                    detail="Assigned user not found"
                )

    # ✅ BUG 6 FIX: Type-Category relationship recheck
    final_category_id = update_data.get("category_id", asset.category_id)
    final_type_id = update_data.get("type_id", asset.type_id)

    # Only validate relationship if either category or type is being updated
    if "category_id" in update_data or "type_id" in update_data:
        asset_type = (
            db.query(AssetType)
            .filter(AssetType.id == final_type_id)
            .first()
        )

        if not asset_type:
            raise HTTPException(
                status_code=404,
                detail="Asset type not found"
            )

        if asset_type.category_id != final_category_id:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Asset type does not belong "
                    "to selected category"
                )
            )

    # Update status based on assigned user changes
    if "assigned_to_user_id" in update_data:
        update_data["status"] = "ASSIGNED" if update_data["assigned_to_user_id"] else "AVAILABLE"

    # Apply all updates
    for key, value in update_data.items():
        setattr(asset, key, value)

    db.commit()
    db.refresh(asset)

    return asset


def deactivate_asset(db, asset_id: str, current_user):
    asset = get_asset_by_id(db, asset_id, current_user)

    asset.is_active = False
    db.commit()
    db.refresh(asset)

    return asset