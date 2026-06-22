from datetime import datetime
import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.asset import Asset, AssetScanLog
from app.models.subscription import Subscription
from app.models.asset_categories import AssetCategory
from app.models.asset_type import AssetType
from app.models.departments import Department
from app.models.users import User
from app.schemas.assets import AssetVerificationRequest
from app.utils.qr import generate_asset_qr


def create_asset(
    db: Session,
    asset_data,
    current_user
):
    # Handle client_id for ADMIN
    if current_user["role"] == "ADMIN":
        if not hasattr(asset_data, 'client_id') or not asset_data.client_id:
            raise HTTPException(
                status_code=400,
                detail="Platform Admin must specify client_id"
            )
        client_id = asset_data.client_id
    else:
        client_id = current_user["client_id"]

    # Validate subscription
    subscription = (
        db.query(Subscription)
        .filter(
            Subscription.client_id == client_id,
            Subscription.status == "ACTIVE"
        )
        .first()
    )

    if not subscription:
        raise HTTPException(
            status_code=400,
            detail="No active subscription found"
        )

    # Check asset limit
    asset_count = (
        db.query(Asset)
        .filter(
            Asset.client_id == client_id,
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

    # Check serial number uniqueness
    if asset_data.serial_number:
        existing_asset = (
            db.query(Asset)
            .filter(
                Asset.client_id == client_id,
                Asset.serial_number == asset_data.serial_number,
                Asset.is_active == True
            )
            .first()
        )

        if existing_asset:
            raise HTTPException(
                status_code=400,
                detail="Serial number already exists"
            )

    # Category validation with global support
    category = (
        db.query(AssetCategory)
        .filter(
            AssetCategory.id == asset_data.category_id,
            AssetCategory.is_active == True,
            or_(
                AssetCategory.client_id == client_id,
                AssetCategory.client_id.is_(None)
            )
        )
        .first()
    )

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Asset category not found"
        )

    # Type validation with global support
    asset_type = (
        db.query(AssetType)
        .filter(
            AssetType.id == asset_data.type_id,
            AssetType.is_active == True,
            or_(
                AssetType.client_id == client_id,
                AssetType.client_id.is_(None)
            )
        )
        .first()
    )

    if not asset_type:
        raise HTTPException(
            status_code=404,
            detail="Asset type not found"
        )

    # Validate type belongs to category
    if asset_type.category_id != category.id:
        raise HTTPException(
            status_code=400,
            detail=(
                "Asset type does not belong "
                "to selected category"
            )
        )

    # Validate department
    department = (
        db.query(Department)
        .filter(
            Department.id == asset_data.department_id,
            Department.client_id == client_id,
            Department.is_active == True
        )
        .first()
    )

    if not department:
        raise HTTPException(
            status_code=404,
            detail="Department not found"
        )

    # Validate assigned user (if provided)
    assigned_user = None
    assigned_user_id = None
    
    if asset_data.assigned_to_user_id:
        assigned_user = (
            db.query(User)
            .filter(
                User.id == asset_data.assigned_to_user_id,
                User.client_id == client_id,
                User.is_active == True
            )
            .first()
        )

        if not assigned_user:
            raise HTTPException(
                status_code=404,
                detail="Assigned user not found"
            )
        assigned_user_id = assigned_user.id

    # Create asset with new fields
    asset = Asset(
        id=str(uuid.uuid4()),
        client_id=client_id,
        category_id=asset_data.category_id,
        type_id=asset_data.type_id,
        department_id=asset_data.department_id,
        assigned_to_user_id=assigned_user_id,

        name=asset_data.name,
        description=asset_data.description,
        serial_number=asset_data.serial_number,
        model=asset_data.model,
        manufacturer=asset_data.manufacturer,
        purchase_date=asset_data.purchase_date,
        purchase_value=asset_data.purchase_value,

        # NEW FIELDS - Status replaced with asset_condition and tag_state
        asset_condition="ACTIVE",
        tag_state="NOT_TAGGED",

        current_latitude=None,
        current_longitude=None,
        last_scanned_by=None,
        last_scanned_at=None,

        qr_code_url=None,
        created_image_url=asset_data.created_image_url if hasattr(asset_data, 'created_image_url') else None,
        latest_image_url=None,
        remarks=None,

        created_by=current_user["id"],
        is_active=True
    )

    # Save asset first
    db.add(asset)
    db.commit()
    db.refresh(asset)

    # Generate QR code after asset is saved
    try:
        qr_url = generate_asset_qr(asset.id)
        asset.qr_code_url = qr_url
        db.commit()
        db.refresh(asset)
    except Exception as e:
        print(f"QR generation failed: {e}")
        # Don't fail asset creation if QR generation fails

    return asset


def get_assets(db: Session, current_user: dict):
    """
    Fetch assets based on role and permissions.
    
    ADMIN → All assets across all clients
    CLIENT_ADMIN → All assets of their client
    MANAGER → Assets belonging to departments they manage
    USER + ASSET_MANAGEMENT.read → All assets of their client
    Normal USER → Only assets assigned to them
    """
    role = current_user["role"]

    # ====================================
    # ADMIN
    # ====================================
    if role == "ADMIN":
        return (
            db.query(Asset)
            .filter(Asset.is_active == True)
            .all()
        )

    # ====================================
    # CLIENT ADMIN
    # ====================================
    if role == "CLIENT_ADMIN":
        return (
            db.query(Asset)
            .filter(
                Asset.client_id == current_user["client_id"],
                Asset.is_active == True
            )
            .all()
        )

    # ====================================
    # MANAGER
    # ====================================
    if role == "MANAGER":
        department_ids = (
            db.query(Department.id)
            .filter(
                Department.manager_id == current_user["id"],
                Department.is_active == True
            )
            .all()
        )

        department_ids = [d[0] for d in department_ids]

        if not department_ids:
            return []

        return (
            db.query(Asset)
            .filter(
                Asset.department_id.in_(department_ids),
                Asset.is_active == True
            )
            .all()
        )

    # ====================================
    # CUSTOM USER WITH ASSET PERMISSION
    # ====================================
    from app.config.permission import has_permission
    
    if has_permission(
        db,
        current_user,
        "ASSET_MANAGEMENT",
        "read"
    ):
        return (
            db.query(Asset)
            .filter(
                Asset.client_id == current_user["client_id"],
                Asset.is_active == True
            )
            .all()
        )

    # ====================================
    # NORMAL USER
    # ====================================
    return (
        db.query(Asset)
        .filter(
            Asset.assigned_to_user_id == current_user["id"],
            Asset.is_active == True
        )
        .all()
    )


def get_asset_by_id(db: Session, asset_id: str, current_user: dict) -> Asset:
    """
    Fetch asset by ID with RBAC validation.
    
    ADMIN → Any asset
    CLIENT_ADMIN → Any asset in their client
    MANAGER → Only assets in departments they manage
    USER + ASSET_MANAGEMENT.read → Any asset in their client
    Normal USER → Only assets assigned to them
    """
    asset = (
        db.query(Asset)
        .filter(
            Asset.id == asset_id,
            Asset.is_active == True
        )
        .first()
    )

    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Asset not found"
        )

    role = current_user["role"]

    # ====================================
    # ADMIN
    # ====================================
    if role == "ADMIN":
        return asset

    # ====================================
    # CLIENT ADMIN
    # ====================================
    if role == "CLIENT_ADMIN":
        if asset.client_id != current_user["client_id"]:
            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )
        return asset

    # ====================================
    # MANAGER
    # ====================================
    if role == "MANAGER":
        department = (
            db.query(Department)
            .filter(
                Department.id == asset.department_id,
                Department.manager_id == current_user["id"],
                Department.is_active == True
            )
            .first()
        )

        if not department:
            raise HTTPException(
                status_code=403,
                detail="You do not manage this asset's department"
            )
        return asset

    # ====================================
    # CUSTOM USER WITH ASSET PERMISSION
    # ====================================
    from app.config.permission import has_permission
    
    if has_permission(
        db,
        current_user,
        "ASSET_MANAGEMENT",
        "read"
    ):
        if asset.client_id != current_user["client_id"]:
            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )
        return asset

    # ====================================
    # NORMAL USER
    # ====================================
    if asset.assigned_to_user_id != current_user["id"]:
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    return asset


def update_asset(db: Session, asset_id: str, asset_data, current_user: dict) -> Asset:
    """
    Update an existing asset.
    RBAC is handled by get_asset_by_id()
    """
    # RBAC validation
    asset = get_asset_by_id(db, asset_id, current_user)

    update_data = asset_data.model_dump(exclude_unset=True)

    # ============================
    # Serial Number Validation
    # ============================
    if "serial_number" in update_data and update_data["serial_number"]:
        existing = (
            db.query(Asset)
            .filter(
                Asset.serial_number == update_data["serial_number"],
                Asset.id != asset_id,
                Asset.is_active == True
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=400,
                detail="Serial number already exists"
            )

    # ============================
    # Category Validation
    # ============================
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

        if (
            current_user["role"] != "ADMIN"
            and category.client_id is not None
            and category.client_id != current_user["client_id"]
        ):
            raise HTTPException(
                status_code=403,
                detail="Category does not belong to your client"
            )

    # ============================
    # Type Validation
    # ============================
    if "type_id" in update_data:
        asset_type = (
            db.query(AssetType)
            .filter(
                AssetType.id == update_data["type_id"],
                AssetType.is_active == True
            )
            .first()
        )

        if not asset_type:
            raise HTTPException(
                status_code=404,
                detail="Asset type not found"
            )

        if (
            current_user["role"] != "ADMIN"
            and asset_type.client_id is not None
            and asset_type.client_id != current_user["client_id"]
        ):
            raise HTTPException(
                status_code=403,
                detail="Asset type does not belong to your client"
            )

        category_id = update_data.get("category_id", asset.category_id)
        
        if asset_type.category_id != category_id:
            raise HTTPException(
                status_code=400,
                detail="Type does not belong to selected category"
            )

    # ============================
    # Department Validation
    # ============================
    if "department_id" in update_data:
        department = (
            db.query(Department)
            .filter(
                Department.id == update_data["department_id"],
                Department.is_active == True
            )
            .first()
        )

        if not department:
            raise HTTPException(
                status_code=404,
                detail="Department not found"
            )

        if (
            current_user["role"] != "ADMIN"
            and department.client_id != current_user["client_id"]
        ):
            raise HTTPException(
                status_code=403,
                detail="Department does not belong to your client"
            )

    # ============================
    # Assigned User Validation
    # ============================
    if "assigned_to_user_id" in update_data:
        if update_data["assigned_to_user_id"]:
            user = (
                db.query(User)
                .filter(
                    User.id == update_data["assigned_to_user_id"],
                    User.is_active == True
                )
                .first()
            )

            if not user:
                raise HTTPException(
                    status_code=404,
                    detail="User not found"
                )

            if (
                current_user["role"] != "ADMIN"
                and user.client_id != current_user["client_id"]
            ):
                raise HTTPException(
                    status_code=403,
                    detail="User does not belong to your client"
                )

    # ============================
    # Update Fields
    # ============================
    for key, value in update_data.items():
        setattr(asset, key, value)

    db.commit()
    db.refresh(asset)

    return asset


def deactivate_asset(db: Session, asset_id: str, current_user: dict) -> Asset:
    """
    Soft delete an asset (set is_active = False).
    RBAC is handled by get_asset_by_id()
    """
    asset = get_asset_by_id(db, asset_id, current_user)

    if not asset.is_active:
        raise HTTPException(
            status_code=400,
            detail="Asset is already deactivated"
        )

    asset.is_active = False
    db.commit()
    db.refresh(asset)

    return asset


def restore_asset(db: Session, asset_id: str, current_user: dict) -> Asset:
    """
    Restore a deactivated asset (set is_active = True).
    """
    asset = (
        db.query(Asset)
        .filter(Asset.id == asset_id)
        .first()
    )

    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Asset not found"
        )

    # Reuse RBAC validation
    get_asset_by_id(db, asset_id, current_user)

    if asset.is_active:
        raise HTTPException(
            status_code=400,
            detail="Asset is already active"
        )

    asset.is_active = True
    db.commit()
    db.refresh(asset)

    return asset


def assign_asset(
    db: Session,
    asset_id: str,
    user_id: str,
    current_user: dict
) -> Asset:
    """
    Assign an asset to a user.
    """
    asset = get_asset_by_id(db, asset_id, current_user)

    user = (
        db.query(User)
        .filter(
            User.id == user_id,
            User.is_active == True
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Client isolation
    if current_user["role"] != "ADMIN":
        if user.client_id != current_user["client_id"]:
            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )

    # Manager restrictions
    if current_user["role"] == "MANAGER":
        department = (
            db.query(Department)
            .filter(
                Department.manager_id == current_user["id"],
                Department.is_active == True
            )
            .first()
        )

        if not department:
            raise HTTPException(
                status_code=403,
                detail="No department assigned"
            )

        if asset.department_id != department.id:
            raise HTTPException(
                status_code=403,
                detail="Asset does not belong to your department"
            )

        if user.department_id != department.id:
            raise HTTPException(
                status_code=403,
                detail="User does not belong to your department"
            )

        # For MANAGER, restrict cross-department assignment
        if asset.department_id != user.department_id:
            raise HTTPException(
                status_code=400,
                detail="Asset and user belong to different departments"
            )

    # Prevent duplicate assignment
    if asset.assigned_to_user_id == user.id:
        raise HTTPException(
            status_code=400,
            detail="Asset already assigned to this user"
        )

    asset.assigned_to_user_id = user.id
    db.commit()
    db.refresh(asset)

    return asset


def unassign_asset(
    db: Session,
    asset_id: str,
    current_user: dict
) -> Asset:
    """
    Unassign an asset from its current user.
    """
    asset = get_asset_by_id(db, asset_id, current_user)

    # Manager restrictions
    if current_user["role"] == "MANAGER":
        department = (
            db.query(Department)
            .filter(
                Department.manager_id == current_user["id"],
                Department.is_active == True
            )
            .first()
        )

        if not department:
            raise HTTPException(
                status_code=403,
                detail="No department assigned"
            )

        if asset.department_id != department.id:
            raise HTTPException(
                status_code=403,
                detail="Asset does not belong to your department"
            )

    if not asset.assigned_to_user_id:
        raise HTTPException(
            status_code=400,
            detail="Asset is already unassigned"
        )

    asset.assigned_to_user_id = None
    db.commit()
    db.refresh(asset)

    return asset


# ============================================
# QR VERIFICATION FUNCTIONS (Coming Next)
# ============================================

def get_asset_verification(db: Session, asset_id: str, current_user: dict):
    """
    Get asset verification details.
    """
    asset = get_asset_by_id(db, asset_id, current_user)
    return asset

def verify_asset(
    db: Session,
    asset_id: str,
    verification_data: AssetVerificationRequest,
    current_user: dict
):
    asset = get_asset_by_id(
        db,
        asset_id,
        current_user
    )

    now = datetime.utcnow()

    asset.current_latitude = verification_data.latitude
    asset.current_longitude = verification_data.longitude
    asset.asset_condition = verification_data.asset_condition
    asset.latest_image_url = verification_data.image_url
    asset.remarks = verification_data.remarks
    asset.last_scanned_by = current_user["id"]
    asset.last_scanned_at = now
    asset.tag_state = "TAGGED"

    scan_log = AssetScanLog(
        id=str(uuid.uuid4()),
        asset_id=asset.id,
        latitude=verification_data.latitude,
        longitude=verification_data.longitude,
        image_url=verification_data.image_url,
        remarks=verification_data.remarks,  # ✅ FIXED: 'notes' -> 'remarks'
        asset_condition=verification_data.asset_condition,
        tag_state="TAGGED",
        verification_type="INITIAL_TAGGING",  # Add this to track first tag
        scanned_by=current_user["id"],
        scanned_at=now
    )

    db.add(scan_log)
    db.commit()
    db.refresh(asset)

    return asset

from app.models.asset import AssetScanLog


def get_asset_audits(
    db: Session,
    asset_id: str,
    current_user: dict
):
    """
    Fetch complete scan history of an asset.
    """

    asset = get_asset_by_id(
        db,
        asset_id,
        current_user
    )

    audits = (
        db.query(AssetScanLog)
        .filter(
            AssetScanLog.asset_id == asset.id
        )
        .order_by(
            AssetScanLog.scanned_at.desc()
        )
        .all()
    )

    return audits


def get_asset_verification_data(
    db: Session,
    asset_id: str,
    current_user: dict
):
    asset = get_asset_by_id(
        db,
        asset_id,
        current_user
    )

    return {
        "asset_id": asset.id,
        "name": asset.name,
        "manufacturer": asset.manufacturer,
        "serial_number": asset.serial_number,
        "model": asset.model,
        "purchase_value": asset.purchase_value,
        "tag_state": asset.tag_state,
        "asset_condition": asset.asset_condition,
        "department_name":
            asset.department.name
            if asset.department
            else None,
        "created_image_url":
            asset.created_image_url
    }



def get_asset_verification_data(
    db: Session,
    asset_id: str,
    current_user: dict
):
    asset = get_asset_by_id(
        db,
        asset_id,
        current_user
    )

    return {
        "asset_id": asset.id,
        "name": asset.name,
        "manufacturer": asset.manufacturer,
        "serial_number": asset.serial_number,
        "model": asset.model,
        "purchase_value": asset.purchase_value,

        "asset_condition": asset.asset_condition,
        "tag_state": asset.tag_state,

        "category_name":
            asset.category.name
            if asset.category
            else None,

        "type_name":
            asset.asset_type.name
            if asset.asset_type
            else None,

        "department_name":
            asset.department.name
            if asset.department
            else None,

        "created_image_url":
            asset.created_image_url,

        "latest_image_url":
            asset.latest_image_url,

        "qr_code_url":
            asset.qr_code_url,

        "current_latitude":
            asset.current_latitude,

        "current_longitude":
            asset.current_longitude
    }

def get_asset_location(
    db: Session,
    asset_id: str,
    current_user: dict
):
    """
    Fetch latest location of asset.
    """

    asset = get_asset_by_id(
        db,
        asset_id,
        current_user
    )

    return {
        "asset_id": asset.id,
        "latitude": asset.current_latitude,
        "longitude": asset.current_longitude,
        "tag_state": asset.tag_state,
        "asset_condition": asset.asset_condition,
        "last_scanned_by": asset.last_scanned_by,
        "last_scanned_at": asset.last_scanned_at
    }



def get_asset_qr(
    db: Session,
    asset_id: str,
    current_user: dict
):
    """
    Fetch QR code details of an asset.
    """

    asset = get_asset_by_id(
        db,
        asset_id,
        current_user
    )

    return {
        "asset_id": asset.id,
        "asset_name": asset.name,
        "qr_code_url": asset.qr_code_url,
        "tag_state": asset.tag_state
    }



from app.utils.qr import generate_asset_qr
from fastapi import HTTPException


def regenerate_asset_qr(
    db: Session,
    asset_id: str,
    current_user: dict
):
    """
    Generate a fresh QR code and update the asset.
    """

    asset = get_asset_by_id(
        db,
        asset_id,
        current_user
    )

    # Managers can only update
    # departments they manage.
    if current_user["role"] == "MANAGER":
        managed_departments = get_managed_department_ids(
            db,
            current_user["id"]
        )

        if asset.department_id not in managed_departments:
            raise HTTPException(
                status_code=403,
                detail="Access denied."
            )

    try:
        qr_url = generate_asset_qr(
            asset.id
        )

        asset.qr_code_url = qr_url

        db.commit()
        db.refresh(asset)

        return {
            "asset_id": asset.id,
            "asset_name": asset.name,
            "qr_code_url": asset.qr_code_url,
            "tag_state": asset.tag_state
        }

    except Exception as e:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Failed to regenerate QR: {str(e)}"
        )