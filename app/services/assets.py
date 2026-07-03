from datetime import datetime
import json
import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.Audit_trail import AuditTrail
from app.models.asset import Asset, AssetScanLog
from app.models.maintenance_task import MaintenanceTask
from app.models.subscription import Subscription
from app.models.asset_categories import AssetCategory
from app.models.asset_type import AssetType
from app.models.departments import Department
from app.models.transfers import Transfer
from app.models.users import User
from app.models.location import Location
from app.schemas.assets import AssetBulkCreate, AssetVerificationRequest, CreateMaintenanceRequest, MarkLostRequest, RejectMaintenanceRequest
from app.utils.qr import generate_asset_qr
from datetime import datetime, timezone



# ============================================
# HELPER: BUILD LOCATION PATH
# ============================================
def build_location_path(location):
    """
    Builds the complete hierarchical path for a location.
    
    Example:
    Office 12 → Floor 8 → Corporate Office → New Delhi → Delhi → India
    
    Returns:
    [
        {"id": "country_id", "name": "India", "location_type": "COUNTRY"},
        {"id": "state_id", "name": "Delhi", "location_type": "STATE"},
        {"id": "city_id", "name": "New Delhi", "location_type": "CITY"},
        {"id": "building_id", "name": "Corporate Office", "location_type": "BUILDING"},
        {"id": "floor_id", "name": "Floor 8", "location_type": "FLOOR"},
        {"id": "office_id", "name": "Office 12", "location_type": "OFFICE"}
    ]
    """
    if not location:
        return None
    
    path = []
    current = location

    while current:
        path.append({
            "id": current.id,
            "name": current.name,
            "location_type": current.location_type
        })
        current = current.parent

    path.reverse()
    return path


def get_location_details(location):
    """
    Returns location details with full path.
    """
    if not location:
        return None
    
    return {
        "id": location.id,
        "path": build_location_path(location)
    }


# ============================================
# CREATE ASSET
# ============================================
def create_asset(
    db: Session,
    asset_data,
    current_user
):
    """
    Create a new asset.
    Supports:
    - Global and client-specific categories/types
    - Optional assigned user
    - Optional location
    - created_image_url
    - latest_image_url
    - custom_fields
    """

    # =====================================
    # Resolve Client ID
    # =====================================
    if current_user["role"] == "ADMIN":

        if (
            not hasattr(asset_data, "client_id")
            or not asset_data.client_id
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Platform Admin must "
                    "specify client_id"
                )
            )

        client_id = asset_data.client_id

    else:
        client_id = current_user["client_id"]

    # =====================================
    # Validate Subscription
    # =====================================
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

    # =====================================
    # Check Asset Limit
    # =====================================
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

    # =====================================
    # Serial Number Validation
    # =====================================
    if asset_data.serial_number:

        existing_asset = (
            db.query(Asset)
            .filter(
                Asset.client_id == client_id,
                Asset.serial_number
                == asset_data.serial_number,
                Asset.is_active == True
            )
            .first()
        )

        if existing_asset:
            raise HTTPException(
                status_code=400,
                detail="Serial number already exists"
            )

    # =====================================
    # Category Validation
    # =====================================
    category = (
        db.query(AssetCategory)
        .filter(
            AssetCategory.id
            == asset_data.category_id,
            AssetCategory.is_active == True,
            or_(
                AssetCategory.client_id
                == client_id,
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

    # =====================================
    # Type Validation
    # =====================================
    asset_type = (
        db.query(AssetType)
        .filter(
            AssetType.id
            == asset_data.type_id,
            AssetType.is_active == True,
            or_(
                AssetType.client_id
                == client_id,
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

    # =====================================
    # Validate Type Belongs to Category
    # =====================================
    if asset_type.category_id != category.id:
        raise HTTPException(
            status_code=400,
            detail=(
                "Asset type does not belong "
                "to selected category"
            )
        )

    # =====================================
    # Department Validation
    # =====================================
    department = (
        db.query(Department)
        .filter(
            Department.id
            == asset_data.department_id,
            Department.client_id
            == client_id,
            Department.is_active == True
        )
        .first()
    )

    if not department:
        raise HTTPException(
            status_code=404,
            detail="Department not found"
        )

    # =====================================
    # Assigned User Validation
    # =====================================
    assigned_user_id = None

    if asset_data.assigned_to_user_id:

        assigned_user = (
            db.query(User)
            .filter(
                User.id
                == asset_data.assigned_to_user_id,
                User.client_id
                == client_id,
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

    # =====================================
    # Location Validation
    # =====================================
    location_id = None

    if (
        hasattr(asset_data, "location_id")
        and asset_data.location_id
    ):
        location = (
            db.query(Location)
            .filter(
                Location.id
                == asset_data.location_id,
                Location.client_id
                == client_id,
                Location.is_active == True
            )
            .first()
        )

        if not location:
            raise HTTPException(
                status_code=404,
                detail="Location not found"
            )

        location_id = location.id

    # =====================================
    # Custom Fields
    # =====================================
    custom_fields = []

    if (
        hasattr(asset_data, "custom_fields")
        and asset_data.custom_fields
    ):
        custom_fields = [
            (
                field.model_dump()
                if hasattr(
                    field,
                    "model_dump"
                )
                else field
            )
            for field in asset_data.custom_fields
        ]

    # =====================================
    # Images
    # =====================================
    created_image_url = (
        asset_data.created_image_url
        if hasattr(
            asset_data,
            "created_image_url"
        )
        else None
    )

    latest_image_url = (
        asset_data.latest_image_url
        if (
            hasattr(
                asset_data,
                "latest_image_url"
            )
            and asset_data.latest_image_url
        )
        else created_image_url
    )

    # =====================================
    # Create Asset
    # =====================================
    asset = Asset(
        id=str(uuid.uuid4()),

        client_id=client_id,
        category_id=asset_data.category_id,
        type_id=asset_data.type_id,
        department_id=asset_data.department_id,
        assigned_to_user_id=assigned_user_id,
        location_id=location_id,

        name=asset_data.name,
        description=asset_data.description,
        serial_number=asset_data.serial_number,
        model=asset_data.model,
        manufacturer=asset_data.manufacturer,
        purchase_date=asset_data.purchase_date,
        purchase_value=asset_data.purchase_value,

        asset_condition="ACTIVE",
        tag_state="NOT_TAGGED",

        current_latitude=None,
        current_longitude=None,
        last_scanned_by=None,
        last_scanned_at=None,

        qr_code_url=None,

        created_image_url=created_image_url,
        latest_image_url=latest_image_url,

        remarks=None,

        custom_fields=custom_fields,

        created_by=current_user["id"],
        is_active=True
    )

    # =====================================
    # Save Asset
    # =====================================
    db.add(asset)
    db.commit()
    db.refresh(asset)

    # =====================================
    # Generate QR Code
    # =====================================
    try:
        qr_url = generate_asset_qr(asset.id)

        asset.qr_code_url = qr_url

        db.commit()
        db.refresh(asset)

    except Exception as e:
        print(
            f"QR generation failed: {e}"
        )

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


def get_asset_by_id(db: Session, asset_id: str, current_user: dict):
    """
    Fetch asset by ID with RBAC validation and location path.
    
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
        pass  # Allow access

    # ====================================
    # CLIENT ADMIN
    # ====================================
    elif role == "CLIENT_ADMIN":
        if asset.client_id != current_user["client_id"]:
            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )

    # ====================================
    # MANAGER
    # ====================================
    elif role == "MANAGER":
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

    # ====================================
    # CUSTOM USER WITH ASSET PERMISSION
    # ====================================
    else:
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
        else:
            # ====================================
            # NORMAL USER
            # ====================================
            if asset.assigned_to_user_id != current_user["id"]:
                raise HTTPException(
                    status_code=403,
                    detail="Access denied"
                )

    # ====================================
    # BUILD RESPONSE WITH LOCATION PATH
    # ====================================
    # Build location data with full path
    location_data = None
    if asset.location:
        location_data = {
        "id": asset.location.id,
        "name": asset.location.name,                       # ✅ ADD THIS
        "location_type": asset.location.location_type,     # ✅ ADD THIS
        "path": build_location_path(asset.location)
    }

    # Convert asset to dict
    asset_dict = {
        "id": asset.id,
        "client_id": asset.client_id,
        "category_id": asset.category_id,
        "type_id": asset.type_id,
        "department_id": asset.department_id,
        "assigned_to_user_id": asset.assigned_to_user_id,
        "location_id": asset.location_id,
        "location": location_data,  # Add location with path
        "name": asset.name,
        "description": asset.description,
        "serial_number": asset.serial_number,
        "model": asset.model,
        "manufacturer": asset.manufacturer,
        "purchase_date": asset.purchase_date,
        "purchase_value": asset.purchase_value,
        "asset_condition": asset.asset_condition,
        "tag_state": asset.tag_state,
        "is_active": asset.is_active,
        "qr_code_url": asset.qr_code_url,
        "created_image_url": asset.created_image_url,
        "latest_image_url": asset.latest_image_url,
        "current_latitude": asset.current_latitude,
        "current_longitude": asset.current_longitude,
        "last_scanned_by": asset.last_scanned_by,
        "last_scanned_at": asset.last_scanned_at,
        "remarks": asset.remarks,
        "created_by": asset.created_by,
        "created_at": asset.created_at,
        "updated_at": asset.updated_at
    }

    return asset_dict


def update_asset(
    db: Session,
    asset_id: str,
    asset_data,
    current_user: dict
):
    """
    Update an existing asset.
    RBAC is handled by get_asset_by_id()
    """

    # RBAC Validation
    get_asset_by_id(
        db=db,
        asset_id=asset_id,
        current_user=current_user
    )

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

    update_data = asset_data.model_dump(
        exclude_unset=True
    )

    # ==========================
    # Serial Number Validation
    # ==========================
    if (
        "serial_number" in update_data
        and update_data["serial_number"]
    ):
        existing = (
            db.query(Asset)
            .filter(
                Asset.serial_number
                == update_data["serial_number"],
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

    # ==========================
    # Category Validation
    # ==========================
    if "category_id" in update_data:

        category = (
            db.query(AssetCategory)
            .filter(
                AssetCategory.id
                == update_data["category_id"],
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
            and category.client_id
            and category.client_id
            != current_user["client_id"]
        ):
            raise HTTPException(
                status_code=403,
                detail=(
                    "Category does not belong "
                    "to your client"
                )
            )

    # ==========================
    # Type Validation
    # ==========================
    if "type_id" in update_data:

        asset_type = (
            db.query(AssetType)
            .filter(
                AssetType.id
                == update_data["type_id"],
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
            and asset_type.client_id
            and asset_type.client_id
            != current_user["client_id"]
        ):
            raise HTTPException(
                status_code=403,
                detail=(
                    "Asset type does not belong "
                    "to your client"
                )
            )

        category_id = update_data.get(
            "category_id",
            asset.category_id
        )

        if asset_type.category_id != category_id:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Type does not belong to "
                    "selected category"
                )
            )

    # ==========================
    # Department Validation
    # ==========================
    if (
        "department_id" in update_data
        and update_data["department_id"]
    ):
        department = (
            db.query(Department)
            .filter(
                Department.id
                == update_data["department_id"],
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
            and department.client_id
            != current_user["client_id"]
        ):
            raise HTTPException(
                status_code=403,
                detail=(
                    "Department does not belong "
                    "to your client"
                )
            )

    # ==========================
    # Assigned User Validation
    # ==========================
    if (
        "assigned_to_user_id" in update_data
        and update_data["assigned_to_user_id"]
    ):
        user = (
            db.query(User)
            .filter(
                User.id
                == update_data["assigned_to_user_id"],
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
            and user.client_id
            != current_user["client_id"]
        ):
            raise HTTPException(
                status_code=403,
                detail=(
                    "User does not belong "
                    "to your client"
                )
            )

    # ==========================
    # Location Validation
    # ==========================
    if (
        "location_id" in update_data
        and update_data["location_id"]
    ):
        location = (
            db.query(Location)
            .filter(
                Location.id
                == update_data["location_id"],
                Location.client_id
                == asset.client_id,
                Location.is_active == True
            )
            .first()
        )

        if not location:
            raise HTTPException(
                status_code=404,
                detail="Location not found"
            )

    # ==========================
    # Custom Fields
    # ==========================
    if (
        "custom_fields" in update_data
        and update_data["custom_fields"]
        is not None
    ):
        update_data["custom_fields"] = [
            (
                field.model_dump()
                if hasattr(
                    field,
                    "model_dump"
                )
                else field
            )
            for field in asset_data.custom_fields
        ]

    # ==========================
    # Update Fields
    # ==========================
    for key, value in update_data.items():
        setattr(asset, key, value)

    db.commit()
    db.refresh(asset)

    # ==========================
    # Location Path Response
    # ==========================
    location_data = None

    if asset.location:
        location_data = {
            "id": asset.location.id,
            "path": build_location_path(
                asset.location
            )
        }

    return {
        "id": asset.id,
        "client_id": asset.client_id,
        "category_id": asset.category_id,
        "type_id": asset.type_id,
        "department_id": asset.department_id,
        "assigned_to_user_id":
            asset.assigned_to_user_id,
        "location_id": asset.location_id,
        "location": location_data,
        "name": asset.name,
        "description": asset.description,
        "serial_number":
            asset.serial_number,
        "model": asset.model,
        "manufacturer":
            asset.manufacturer,
        "purchase_date":
            asset.purchase_date,
        "purchase_value":
            asset.purchase_value,
        "asset_condition":
            asset.asset_condition,
        "tag_state":
            asset.tag_state,
        "is_active":
            asset.is_active,
        "qr_code_url":
            asset.qr_code_url,
        "created_image_url":
            asset.created_image_url,
        "latest_image_url":
            asset.latest_image_url,
        "custom_fields":
            asset.custom_fields,
        "current_latitude":
            asset.current_latitude,
        "current_longitude":
            asset.current_longitude,
        "last_scanned_by":
            asset.last_scanned_by,
        "last_scanned_at":
            asset.last_scanned_at,
        "remarks":
            asset.remarks,
        "created_by":
            asset.created_by,
        "created_at":
            asset.created_at,
        "updated_at":
            asset.updated_at
    }
def deactivate_asset(db: Session, asset_id: str, current_user: dict):
    """
    Soft delete an asset (set is_active = False).
    """
    asset_dict = get_asset_by_id(db, asset_id, current_user)
    
    asset = (
        db.query(Asset)
        .filter(Asset.id == asset_id)
        .first()
    )

    if not asset.is_active:
        raise HTTPException(
            status_code=400,
            detail="Asset is already deactivated"
        )

    asset.is_active = False
    db.commit()
    db.refresh(asset)

    # Return with location path
    location_data = None
    if asset.location:
        location_data = {
            "id": asset.location.id,
            "path": build_location_path(asset.location)
        }

    return {
        "id": asset.id,
        "client_id": asset.client_id,
        "category_id": asset.category_id,
        "type_id": asset.type_id,
        "department_id": asset.department_id,
        "assigned_to_user_id": asset.assigned_to_user_id,
        "location_id": asset.location_id,
        "location": location_data,
        "name": asset.name,
        "description": asset.description,
        "serial_number": asset.serial_number,
        "model": asset.model,
        "manufacturer": asset.manufacturer,
        "purchase_date": asset.purchase_date,
        "purchase_value": asset.purchase_value,
        "asset_condition": asset.asset_condition,
        "tag_state": asset.tag_state,
        "is_active": asset.is_active,
        "qr_code_url": asset.qr_code_url,
        "created_image_url": asset.created_image_url,
        "latest_image_url": asset.latest_image_url,
        "current_latitude": asset.current_latitude,
        "current_longitude": asset.current_longitude,
        "last_scanned_by": asset.last_scanned_by,
        "last_scanned_at": asset.last_scanned_at,
        "remarks": asset.remarks,
        "created_by": asset.created_by,
        "created_at": asset.created_at,
        "updated_at": asset.updated_at
    }


def restore_asset(db: Session, asset_id: str, current_user: dict):
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

    # Return with location path
    location_data = None
    if asset.location:
        location_data = {
            "id": asset.location.id,
            "path": build_location_path(asset.location)
        }

    return {
        "id": asset.id,
        "client_id": asset.client_id,
        "category_id": asset.category_id,
        "type_id": asset.type_id,
        "department_id": asset.department_id,
        "assigned_to_user_id": asset.assigned_to_user_id,
        "location_id": asset.location_id,
        "location": location_data,
        "name": asset.name,
        "description": asset.description,
        "serial_number": asset.serial_number,
        "model": asset.model,
        "manufacturer": asset.manufacturer,
        "purchase_date": asset.purchase_date,
        "purchase_value": asset.purchase_value,
        "asset_condition": asset.asset_condition,
        "tag_state": asset.tag_state,
        "is_active": asset.is_active,
        "qr_code_url": asset.qr_code_url,
        "created_image_url": asset.created_image_url,
        "latest_image_url": asset.latest_image_url,
        "current_latitude": asset.current_latitude,
        "current_longitude": asset.current_longitude,
        "last_scanned_by": asset.last_scanned_by,
        "last_scanned_at": asset.last_scanned_at,
        "remarks": asset.remarks,
        "created_by": asset.created_by,
        "created_at": asset.created_at,
        "updated_at": asset.updated_at
    }


def assign_asset(
    db: Session,
    asset_id: str,
    user_id: str,
    current_user: dict
):
    """
    Assign an asset to a user.
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

    # RBAC validation
    get_asset_by_id(db, asset_id, current_user)

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

    # Return with location path
    location_data = None
    if asset.location:
        location_data = {
            "id": asset.location.id,
            "path": build_location_path(asset.location)
        }

    return {
        "id": asset.id,
        "client_id": asset.client_id,
        "category_id": asset.category_id,
        "type_id": asset.type_id,
        "department_id": asset.department_id,
        "assigned_to_user_id": asset.assigned_to_user_id,
        "location_id": asset.location_id,
        "location": location_data,
        "name": asset.name,
        "description": asset.description,
        "serial_number": asset.serial_number,
        "model": asset.model,
        "manufacturer": asset.manufacturer,
        "purchase_date": asset.purchase_date,
        "purchase_value": asset.purchase_value,
        "asset_condition": asset.asset_condition,
        "tag_state": asset.tag_state,
        "is_active": asset.is_active,
        "qr_code_url": asset.qr_code_url,
        "created_image_url": asset.created_image_url,
        "latest_image_url": asset.latest_image_url,
        "current_latitude": asset.current_latitude,
        "current_longitude": asset.current_longitude,
        "last_scanned_by": asset.last_scanned_by,
        "last_scanned_at": asset.last_scanned_at,
        "remarks": asset.remarks,
        "created_by": asset.created_by,
        "created_at": asset.created_at,
        "updated_at": asset.updated_at
    }


def unassign_asset(
    db: Session,
    asset_id: str,
    current_user: dict
):
    """
    Unassign an asset from its current user.
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

    # RBAC validation
    get_asset_by_id(db, asset_id, current_user)

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

    # Return with location path
    location_data = None
    if asset.location:
        location_data = {
            "id": asset.location.id,
            "path": build_location_path(asset.location)
        }

    return {
        "id": asset.id,
        "client_id": asset.client_id,
        "category_id": asset.category_id,
        "type_id": asset.type_id,
        "department_id": asset.department_id,
        "assigned_to_user_id": asset.assigned_to_user_id,
        "location_id": asset.location_id,
        "location": location_data,
        "name": asset.name,
        "description": asset.description,
        "serial_number": asset.serial_number,
        "model": asset.model,
        "manufacturer": asset.manufacturer,
        "purchase_date": asset.purchase_date,
        "purchase_value": asset.purchase_value,
        "asset_condition": asset.asset_condition,
        "tag_state": asset.tag_state,
        "is_active": asset.is_active,
        "qr_code_url": asset.qr_code_url,
        "created_image_url": asset.created_image_url,
        "latest_image_url": asset.latest_image_url,
        "current_latitude": asset.current_latitude,
        "current_longitude": asset.current_longitude,
        "last_scanned_by": asset.last_scanned_by,
        "last_scanned_at": asset.last_scanned_at,
        "remarks": asset.remarks,
        "created_by": asset.created_by,
        "created_at": asset.created_at,
        "updated_at": asset.updated_at
    }


# ============================================
# QR VERIFICATION FUNCTIONS
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

    # RBAC validation
    get_asset_by_id(db, asset_id, current_user)

    now = datetime.now(timezone.utc)

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
        remarks=verification_data.remarks,
        asset_condition=verification_data.asset_condition,
        tag_state="TAGGED",
        verification_type="INITIAL_TAGGING",
        scanned_by=current_user["id"],
        scanned_at=now
    )

    db.add(scan_log)
    db.commit()
    db.refresh(asset)

    # Return with location path
    location_data = None
    if asset.location:
        location_data = {
            "id": asset.location.id,
            "path": build_location_path(asset.location)
        }

    return {
        "id": asset.id,
        "client_id": asset.client_id,
        "category_id": asset.category_id,
        "type_id": asset.type_id,
        "department_id": asset.department_id,
        "assigned_to_user_id": asset.assigned_to_user_id,
        "location_id": asset.location_id,
        "location": location_data,
        "name": asset.name,
        "description": asset.description,
        "serial_number": asset.serial_number,
        "model": asset.model,
        "manufacturer": asset.manufacturer,
        "purchase_date": asset.purchase_date,
        "purchase_value": asset.purchase_value,
        "asset_condition": asset.asset_condition,
        "tag_state": asset.tag_state,
        "is_active": asset.is_active,
        "qr_code_url": asset.qr_code_url,
        "created_image_url": asset.created_image_url,
        "latest_image_url": asset.latest_image_url,
        "current_latitude": asset.current_latitude,
        "current_longitude": asset.current_longitude,
        "last_scanned_by": asset.last_scanned_by,
        "last_scanned_at": asset.last_scanned_at,
        "remarks": asset.remarks,
        "created_by": asset.created_by,
        "created_at": asset.created_at,
        "updated_at": asset.updated_at
    }


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
            AssetScanLog.asset_id == asset['id']
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
    asset_dict = get_asset_by_id(
        db,
        asset_id,
        current_user
    )

    return {
        "asset_id": asset_dict["id"],
        "name": asset_dict["name"],
        "manufacturer": asset_dict["manufacturer"],
        "serial_number": asset_dict["serial_number"],
        "model": asset_dict["model"],
        "purchase_value": asset_dict["purchase_value"],

        "asset_condition": asset_dict["asset_condition"],
        "tag_state": asset_dict["tag_state"],

        "category_name": None,  # You might want to fetch these separately
        "type_name": None,
        "department_name": None,

        "created_image_url": asset_dict["created_image_url"],
        "latest_image_url": asset_dict["latest_image_url"],
        "qr_code_url": asset_dict["qr_code_url"],
        "current_latitude": asset_dict["current_latitude"],
        "current_longitude": asset_dict["current_longitude"]
    }


def get_asset_location(
    db: Session,
    asset_id: str,
    current_user: dict
):
    """
    Fetch latest location of asset.
    """

    asset_dict = get_asset_by_id(
        db,
        asset_id,
        current_user
    )

    return {
        "asset_id": asset_dict["id"],
        "latitude": asset_dict["current_latitude"],
        "longitude": asset_dict["current_longitude"],
        "tag_state": asset_dict["tag_state"],
        "asset_condition": asset_dict["asset_condition"],
        "last_scanned_by": asset_dict["last_scanned_by"],
        "last_scanned_at": asset_dict["last_scanned_at"]
    }


def get_asset_qr(
    db: Session,
    asset_id: str,
    current_user: dict
):
    """
    Fetch QR code details of an asset.
    """

    asset_dict = get_asset_by_id(
        db,
        asset_id,
        current_user
    )

    return {
        "asset_id": asset_dict["id"],
        "asset_name": asset_dict["name"],
        "qr_code_url": asset_dict["qr_code_url"],
        "tag_state": asset_dict["tag_state"]
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

    asset_dict = get_asset_by_id(
        db,
        asset_id,
        current_user
    )
    
    asset = (
        db.query(Asset)
        .filter(Asset.id == asset_id)
        .first()
    )

    # Managers can only update departments they manage.
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


from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.services.departments import get_managed_department_ids


def get_asset_dashboard(
    db: Session,
    current_user: dict,
    client_id: str | None = None
):
    """
    Fetch asset dashboard statistics.

    Access:
    - ADMIN:
        • Without client_id -> entire platform
        • With client_id -> specific client

    - CLIENT_ADMIN:
        • Own client only

    - MANAGER:
        • Departments they manage only

    - Custom Roles:
        • Own client only
    """

    # Base query
    query = (
        db.query(Asset)
        .filter(
            Asset.is_active == True
        )
    )

    # -------------------------
    # Client Scoping
    # -------------------------

    if current_user["role"] == "ADMIN":
        # Platform admin can optionally filter by client
        if client_id:
            query = query.filter(
                Asset.client_id == client_id
            )

    else:
        # Everyone else sees only their client
        query = query.filter(
            Asset.client_id == current_user["client_id"]
        )

    # -------------------------
    # Department Scoping
    # -------------------------

    if current_user["role"] == "MANAGER":

        department_ids = (
            get_managed_department_ids(
                db,
                current_user["id"]
            )
        )

        query = query.filter(
            Asset.department_id.in_(department_ids)
        )

    # -------------------------
    # Statistics
    # -------------------------

    total_assets = query.count()

    tagged_assets = (
        query.filter(
            Asset.tag_state == "TAGGED"
        ).count()
    )

    not_tagged_assets = (
        query.filter(
            Asset.tag_state == "NOT_TAGGED"
        ).count()
    )

    active_assets = (
        query.filter(
            Asset.asset_condition == "ACTIVE"
        ).count()
    )

    inactive_assets = (
        query.filter(
            Asset.asset_condition == "INACTIVE"
        ).count()
    )

    damaged_assets = (
        query.filter(
            Asset.asset_condition == "DAMAGED"
        ).count()
    )

    maintenance_assets = (
        query.filter(
            Asset.asset_condition == "UNDER_MAINTENANCE"
        ).count()
    )

    lost_assets = (
        query.filter(
            Asset.asset_condition == "LOST"
        ).count()
    )

    return {
        "total_assets": total_assets,
        "tagged_assets": tagged_assets,
        "not_tagged_assets": not_tagged_assets,
        "active_assets": active_assets,
        "inactive_assets": inactive_assets,
        "damaged_assets": damaged_assets,
        "maintenance_assets": maintenance_assets,
        "lost_assets": lost_assets
    }

def bulk_create_assets(
    db: Session,
    payload: AssetBulkCreate,
    client_id: str,
    created_by: str
):
    created_count = 0
    errors = []

    if(payload.client_id and client_id):
        admin_client = db.query(User).filter(User.client_id == client_id, User.role=="CLIENT_ADMIN").first()
        for index, item in enumerate(payload.assets):
            try:
                category = (
                    db.query(AssetCategory)
                    .filter(
                        AssetCategory.client_id == client_id,
                        AssetCategory.id == item.category
                    )
                    .first()
                )

                if not category:
                    raise Exception(
                        f"Category '{item.category}' not found."
                    )

                asset_type = (
                    db.query(AssetType)
                    .filter(
                        AssetType.client_id == client_id,
                        AssetType.id == item.type
                    )
                    .first()
                )

                if not asset_type:
                    raise Exception(
                        f"Type '{item.type}' not found."
                    )

                department = None

                if item.department:
                    department = (
                        db.query(Department)
                        .filter(
                            Department.client_id == client_id,
                            Department.name == item.department
                        )
                        .first()
                    )

                location = None

                if item.location:
                    location = (
                        db.query(Location)
                        .filter(
                            Location.client_id == client_id,
                            Location.name == item.location
                        )
                        .first()
                    )

                asset = Asset(
                    client_id=client_id,
                    category_id=category.id,
                    type_id=asset_type.id,
                    department_id=department.id if department else None,
                    location_id=location.id if location else None,

                    name=item.name,
                    description=item.description,
                    serial_number=item.serial_number,
                    model=item.model,
                    manufacturer=item.manufacturer,
                    purchase_value=item.purchase_value,

                    created_image_url=item.created_image_url,
                    latest_image_url=(
                        item.latest_image_url
                        or item.created_image_url
                    ),

                    created_by=admin_client.id
                )

                db.add(asset)
                created_count += 1

            except Exception as e:
                errors.append({
                    "row": index + 1,
                    "error": str(e)
                })

            db.commit()

    else:
        for index, item in enumerate(payload.assets):

            try:
                category = (
                db.query(AssetCategory)
                .filter(
                    AssetCategory.client_id == client_id,
                    AssetCategory.id == item.category
                )
                .first()
            )

                if not category:
                    raise Exception(
                    f"Category '{item.category}' not found."
                )

                asset_type = (
                db.query(AssetType)
                .filter(
                    AssetType.client_id == client_id,
                    AssetType.id == item.type
                )
                .first()
            )

                if not asset_type:
                    raise Exception(
                    f"Type '{item.type}' not found."
                )

                department = None

                if item.department:
                    department = (
                    db.query(Department)
                    .filter(
                        Department.client_id == client_id,
                        Department.name == item.department
                    )
                    .first()
                )

                location = None

                if item.location:
                    location = (
                    db.query(Location)
                    .filter(
                        Location.client_id == client_id,
                        Location.name == item.location
                    )
                    .first()
                )

                asset = Asset(
                client_id=client_id,
                category_id=category.id,
                type_id=asset_type.id,
                department_id=department.id if department else None,
                location_id=location.id if location else None,

                name=item.name,
                description=item.description,
                serial_number=item.serial_number,
                model=item.model,
                manufacturer=item.manufacturer,
                purchase_value=item.purchase_value,

                created_image_url=item.created_image_url,
                latest_image_url=(
                    item.latest_image_url
                    or item.created_image_url
                ),

                created_by=created_by
            )

                db.add(asset)
                created_count += 1

            except Exception as e:
                errors.append({
                "row": index + 1,
                "error": str(e)
            })

        db.commit()

    return {
        "message": f"{created_count} assets created.",
        "created_count": created_count,
        "failed_count": len(errors),
        "errors": errors
    }
from app.models.asset import Asset
from app.models.departments import Department
from sqlalchemy.orm import Session


def get_asset_condition_stats(
    db: Session,
    current_user: dict,
    client_id: str | None = None
):
    """
    Fetch asset statistics grouped by condition.
    """

    query = (
        db.query(Asset)
        .filter(
            Asset.is_active == True
        )
    )

    # ---------------------
    # Client Filtering
    # ---------------------

    if current_user["role"] == "ADMIN":
        if client_id:
            query = query.filter(
                Asset.client_id == client_id
            )

    else:
        query = query.filter(
            Asset.client_id ==
            current_user["client_id"]
        )

    # ---------------------
    # Manager Filtering
    # ---------------------

    if current_user["role"] == "MANAGER":

        department_ids = [
            department.id
            for department in (
                db.query(Department.id)
                .filter(
                    Department.manager_id
                    == current_user["id"],
                    Department.is_active == True
                )
                .all()
            )
        ]

        query = query.filter(
            Asset.department_id.in_(
                department_ids
            )
        )

    active = (
        query.filter(
            Asset.asset_condition
            == "ACTIVE"
        ).count()
    )

    inactive = (
        query.filter(
            Asset.asset_condition
            == "INACTIVE"
        ).count()
    )

    damaged = (
        query.filter(
            Asset.asset_condition
            == "DAMAGED"
        ).count()
    )

    maintenance = (
        query.filter(
            Asset.asset_condition
            == "UNDER_MAINTENANCE"
        ).count()
    )

    lost = (
        query.filter(
            Asset.asset_condition
            == "LOST"
        ).count()
    )

    return {
        "ACTIVE": active,
        "INACTIVE": inactive,
        "DAMAGED": damaged,
        "UNDER_MAINTENANCE": maintenance,
        "LOST": lost
    }


from app.models.asset import Asset
from app.models.departments import Department
from sqlalchemy.orm import Session


def get_asset_tagging_stats(
    db: Session,
    current_user: dict,
    client_id: str | None = None
):
    """
    Fetch asset statistics grouped
    by tagging state.
    """

    query = (
        db.query(Asset)
        .filter(
            Asset.is_active == True
        )
    )

    # ------------------------
    # Client Filtering
    # ------------------------

    if current_user["role"] == "ADMIN":
        if client_id:
            query = query.filter(
                Asset.client_id == client_id
            )

    else:
        query = query.filter(
            Asset.client_id
            == current_user["client_id"]
        )

    # ------------------------
    # Manager Filtering
    # ------------------------

    if current_user["role"] == "MANAGER":

        department_ids = [
            department.id
            for department in (
                db.query(Department.id)
                .filter(
                    Department.manager_id
                    == current_user["id"],
                    Department.is_active == True
                )
                .all()
            )
        ]

        query = query.filter(
            Asset.department_id.in_(
                department_ids
            )
        )

    tagged = (
        query.filter(
            Asset.tag_state
            == "TAGGED"
        ).count()
    )

    not_tagged = (
        query.filter(
            Asset.tag_state
            == "NOT_TAGGED"
        ).count()
    )

    return {
        "TAGGED": tagged,
        "NOT_TAGGED": not_tagged
    }


from sqlalchemy import or_, asc, desc
from app.models.asset import Asset
from app.models.departments import Department
from sqlalchemy.orm import Session
from sqlalchemy import or_, asc, desc

from app.models.asset import Asset
from app.models.departments import Department

from sqlalchemy import or_, asc, desc
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from datetime import date
from sqlalchemy import or_, asc, desc, and_
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from datetime import date, datetime

def search_assets(
    db: Session,
    current_user: dict,
    q: Optional[str] = None,
    client_id: Optional[str] = None,
    category_id: Optional[str] = None,
    type_id: Optional[str] = None,
    department_id: Optional[str] = None,
    location_id: Optional[str] = None,
    assigned_to_user_id: Optional[str] = None,
    asset_condition: Optional[str] = None,
    tag_state: Optional[str] = None,
    manufacturer: Optional[str] = None,
    serial_number: Optional[str] = None,
    purchase_start_date: Optional[date] = None,
    purchase_end_date: Optional[date] = None,
    last_scanned_from: Optional[datetime] = None,
    last_scanned_to: Optional[datetime] = None,
    created_by: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    page: int = 1,
    limit: int = 20
):
    # --------------------------------
    # Base Query with Eager Loading
    # --------------------------------
    query = (
        db.query(Asset)
        .filter(Asset.is_active == True)
        .options(
            joinedload(Asset.category),
            joinedload(Asset.asset_type),      # ✅ Fixed: asset_type
            joinedload(Asset.department),
            joinedload(Asset.location),
            joinedload(Asset.assigned_to_user) # ✅ Fixed: assigned_to_user
        )
    )

    # --------------------------------
    # Role Filtering
    # --------------------------------
    
    # Platform Admin
    if current_user["role"] == "ADMIN":
        if client_id:
            query = query.filter(Asset.client_id == client_id)

    # Everyone except platform admin
    else:
        query = query.filter(Asset.client_id == current_user["client_id"])

    # Manager
    if current_user["role"] == "MANAGER":
        department_ids = [
            d.id for d in (
                db.query(Department.id)
                .filter(
                    Department.manager_id == current_user["id"],
                    Department.is_active == True
                )
                .all()
            )
        ]
        if not department_ids:
            query = query.filter(False)  # ✅ Cleaner approach
        else:
            query = query.filter(Asset.department_id.in_(department_ids))

    # Normal User (without custom role)
    if current_user["role"] == "USER" and not current_user.get("custom_role_id"):
        query = query.filter(Asset.assigned_to_user_id == current_user["id"])

    # --------------------------------
    # Search with Location Support
    # --------------------------------
    
    if q:
        # Join Location for search
        query = query.outerjoin(Location, Asset.location_id == Location.id)
        
        search_terms = q.strip().split()
        search_filters = []
        
        for term in search_terms:
            search_filters.append(
                or_(
                    Asset.name.ilike(f"%{term}%"),
                    Asset.description.ilike(f"%{term}%"),
                    Asset.model.ilike(f"%{term}%"),
                    Asset.manufacturer.ilike(f"%{term}%"),
                    Asset.serial_number.ilike(f"%{term}%"),
                    Location.name.ilike(f"%{term}%")
                    # ✅ Removed: Asset.asset_tag (doesn't exist)
                )
            )
        
        if search_filters:
            query = query.filter(and_(*search_filters))  # ✅ Changed to AND for better matching

    # --------------------------------
    # Filters
    # --------------------------------
    
    if category_id:
        query = query.filter(Asset.category_id == category_id)
    
    if type_id:
        query = query.filter(Asset.type_id == type_id)  # ✅ Using type_id (foreign key)
    
    if department_id:
        query = query.filter(Asset.department_id == department_id)
    
    if location_id:
        query = query.filter(Asset.location_id == location_id)
    
    if assigned_to_user_id:
        query = query.filter(Asset.assigned_to_user_id == assigned_to_user_id)
    
    if asset_condition:
        query = query.filter(Asset.asset_condition == asset_condition)
    
    if tag_state:
        query = query.filter(Asset.tag_state == tag_state)
    
    if manufacturer:
        query = query.filter(Asset.manufacturer.ilike(f"%{manufacturer}%"))
    
    if serial_number:
        # ✅ Exact match for serial numbers (they're usually unique)
        query = query.filter(Asset.serial_number == serial_number)
    
    if created_by:
        query = query.filter(Asset.created_by == created_by)

    # --------------------------------
    # Date Filters
    # --------------------------------
    
    if purchase_start_date:
        query = query.filter(Asset.purchase_date >= purchase_start_date)
    
    if purchase_end_date:
        query = query.filter(Asset.purchase_date <= purchase_end_date)
    
    if last_scanned_from:
        query = query.filter(Asset.last_scanned_at >= last_scanned_from)
    
    if last_scanned_to:
        query = query.filter(Asset.last_scanned_at <= last_scanned_to)

    # --------------------------------
    # Sorting
    # --------------------------------
    
    sort_order = sort_order.lower()
    if sort_order not in ["asc", "desc"]:
        sort_order = "desc"
    
    sortable_fields = {
        "name": Asset.name,
        "manufacturer": Asset.manufacturer,
        "purchase_date": Asset.purchase_date,
        "created_at": Asset.created_at,
        "serial_number": Asset.serial_number,
        "asset_condition": Asset.asset_condition,
        "tag_state": Asset.tag_state,
        "last_scanned_at": Asset.last_scanned_at,
        "model": Asset.model
        # ✅ Removed: "asset_tag": Asset.asset_tag
    }
    
    sort_column = sortable_fields.get(sort_by, Asset.created_at)
    
    if sort_order == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column), desc(Asset.created_at))

    # --------------------------------
    # Pagination with Limits
    # --------------------------------
    
    page = max(page, 1)
    limit = max(limit, 1)
    limit = min(limit, 100)  # ✅ Cap to prevent abuse
    
    offset = (page - 1) * limit
    
    # ✅ Use distinct to handle joined tables correctly
    total = query.distinct(Asset.id).count()
    
    assets = (
        query
        .distinct(Asset.id)
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    total_pages = (total + limit - 1) // limit if limit > 0 else 0

    return {
        "items": assets,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1
        }
    }


from sqlalchemy.orm import joinedload
def get_asset_transfers(
    db: Session,
    asset_id: str,
    current_user: dict
):
    """
    Fetch complete transfer history
    of an asset.
    """

    asset = get_asset_by_id(
        db,
        asset_id,
        current_user
    )

    transfers = (
        db.query(Transfer)
        .options(
            joinedload(
                Transfer.from_location
            ),
            joinedload(
                Transfer.to_location
            ),
            joinedload(
                Transfer.from_department
            ),
            joinedload(
                Transfer.to_department
            ),
            joinedload(
                Transfer.from_user
            ),
            joinedload(
                Transfer.to_user
            ),
            joinedload(
                Transfer.transferred_by_user
            )
        )
        .filter(
            Transfer.asset_id
            == asset.get("id")
        )
        .order_by(
            Transfer.transferred_at.desc()
        )
        .all()
    )

    response = []

    for transfer in transfers:
        response.append(
            {
                "id": transfer.id,

                "transfer_type":
                transfer.transfer_type,

                "transfer_reason":
                transfer.transfer_reason,

                "from_location":
                transfer.from_location.name
                if transfer.from_location
                else None,

                "to_location":
                transfer.to_location.name
                if transfer.to_location
                else None,

                "from_department":
                transfer.from_department.name
                if transfer.from_department
                else None,

                "to_department":
                transfer.to_department.name
                if transfer.to_department
                else None,

                "from_user":
                transfer.from_user.full_name
                if transfer.from_user
                else None,

                "to_user":
                transfer.to_user.full_name
                if transfer.to_user
                else None,

                "notes":
                transfer.notes,

                "status":
                transfer.status,

                "transferred_by":
                transfer.transferred_by_user.full_name
                if transfer.transferred_by_user
                else None,

                "transferred_at":
                transfer.transferred_at
            }
        )

    return response



def get_asset_timeline(
    db: Session,
    asset_id: str,
    current_user: dict
):
    asset = get_asset_by_id(
        db,
        asset_id,
        current_user
    )

    timeline = []

    #
    # Asset Created
    #
    timeline.append(
        {
            "event_type": "CREATED",
            "title": "Asset Created",
            "description": asset.name,
            "performed_by": None,
            "created_at": asset.created_at
        }
    )

    #
    # Asset Tagged
    #
    if (
        asset.tag_state == "TAGGED"
        and asset.last_scanned_at
    ):
        timeline.append(
            {
                "event_type": "TAGGED",
                "title": "Asset Tagged",
                "description": (
                    "QR scanned and asset tagged"
                ),
                "performed_by": None,
                "created_at":
                asset.last_scanned_at
            }
        )

    #
    # Scan Logs
    #
    scan_logs = (
        db.query(AssetScanLog)
        .filter(
            AssetScanLog.asset_id
            == asset.id
        )
        .all()
    )

    for scan in scan_logs:
        timeline.append(
            {
                "event_type": "VERIFIED",
                "title": "Asset Verified",
                "description":
                scan.remarks,
                "performed_by":
                scan.scanner.full_name
                if scan.scanner
                else None,
                "created_at":
                scan.scanned_at
            }
        )

    #
    # Transfers
    #
    transfers = (
        db.query(Transfer)
        .filter(
            Transfer.asset_id
            == asset.id
        )
        .all()
    )

    for transfer in transfers:
        timeline.append(
            {
                "event_type":
                "TRANSFERRED",

                "title":
                "Asset Transferred",

                "description":
                transfer.transfer_reason,

                "performed_by":
                transfer
                .transferred_by_user
                .full_name
                if transfer
                .transferred_by_user
                else None,

                "created_at":
                transfer.transferred_at
            }
        )

    #
    # Sort newest first
    #
    timeline.sort(
        key=lambda x:
        x["created_at"],
        reverse=True
    )

    return timeline


def mark_asset_lost(
    db: Session,
    asset_id: str,
    payload: MarkLostRequest,
    current_user: dict
):
    asset = get_asset_by_id(
        db,
        asset_id,
        current_user
    )

    if asset.asset_condition == "LOST":
        raise HTTPException(
            status_code=400,
            detail="Asset is already marked as lost."
        )

    old_condition = asset.asset_condition

    asset.asset_condition = "LOST"

    audit = AuditTrail(
        entity_type="ASSET",
        entity_id=asset.get("id"),
        action="MARK_LOST",
        old_value=old_condition,
        new_value="LOST",
        description=payload.reason,
        performed_by=current_user["id"]
    )

    db.add(audit)

    db.commit()
    db.refresh(asset)

    return asset


def get_asset_timeline(
    db: Session,
    asset_id: str,
    current_user: dict
):
    asset = get_asset_by_id(
        db,
        asset_id,
        current_user
    )

    timeline = []

    #
    # Asset Created
    #
    creator_name = None

    if asset.get("created_by_user"):
        creator_name = (
            asset.get("created_by_user").full_name
        )

    timeline.append(
        {
            "event_type": "CREATED",
            "title": "Asset Created",
            "description":
            f"{asset.get('name')} created",
            "performed_by":
            creator_name,
            "created_at":
            asset.get("created_at")
        }
    )

    #
    # Verification History
    #
    scan_logs = (
        db.query(AssetScanLog)
        .filter(
            AssetScanLog.asset_id
            == asset.get("id")
        )
        .order_by(
            AssetScanLog.scanned_at
        )
        .all()
    )

    for scan in scan_logs:

        scanner_name = None

        if scan.scanner:
            scanner_name = (
                scan.scanner.full_name
            )

        timeline.append(
            {
                "event_type":
                "VERIFIED",

                "title":
                "Asset Verified",

                "description":
                scan.remarks,

                "performed_by":
                scanner_name,

                "created_at":
                scan.scanned_at
            }
        )

    #
    # Transfer History
    #
    transfers = (
        db.query(Transfer)
        .filter(
            Transfer.asset_id
            == asset.get("id")
        )
        .order_by(
            Transfer.transferred_at
        )
        .all()
    )

    for transfer in transfers:

        performed_by = None

        if (
            transfer
            .transferred_by_user
        ):
            performed_by = (
                transfer
                .transferred_by_user
                .full_name
            )

        description = (
            transfer.transfer_reason
            or
            "Asset transferred"
        )

        timeline.append(
            {
                "event_type":
                "TRANSFERRED",

                "title":
                "Asset Transferred",

                "description":
                description,

                "performed_by":
                performed_by,

                "created_at":
                transfer.transferred_at
            }
        )

    #
    # Maintenance
    #
    maintenance_tasks = (
        db.query(MaintenanceTask)
        .filter(
            MaintenanceTask.asset_id
            == asset.get("id")
        )
        .all()
    )

    for task in maintenance_tasks:

        timeline.append(
            {
                "event_type":
                "MAINTENANCE",

                "title":
                "Maintenance Created",

                "description":
                task.issue_description,

                "performed_by":
                None,

                "created_at":
                task.created_at
            }
        )

    #
    # Audit Trail
    #
    audits = (
        db.query(AuditTrail)
        .filter(
            AuditTrail.entity_type
            == "ASSET",
            AuditTrail.entity_id
            == asset.get("id")
        )
        .all()
    )

    for audit in audits:

        timeline.append(
            {
                "event_type":
                audit.action,

                "title":
                audit.action
                .replace("_", " ")
                .title(),

                "description":
                audit.description,

                "performed_by":
                None,

                "created_at":
                audit.created_at
            }
        )

    #
    # Sort Descending
    #
    timeline.sort(
        key=lambda x:
        x["created_at"],
        reverse=True
    )

    return timeline





from datetime import datetime




from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.asset import Asset


def get_my_assets(
    db: Session,
    current_user: dict,
    user_id: str | None = None
):
    
    #for platform admin 
    print("current_user.get('role')",current_user.get("role"))
    print("user_id",user_id)
    if(current_user.get("role") == "ADMIN" and user_id):
        print("CA+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL")
        query=(db.query(Asset).filter(Asset.assigned_to_user_id==user_id,Asset.is_active==True))
        return (
        query
        .order_by(
            Asset.name.asc()
        )
        .all()
    )

    query = (
        db.query(Asset)
        .filter(
            Asset.client_id
            == current_user.get("client_id"),
            Asset.is_active
            == True
        )
    )


    #
    # Manager:
    # - Own assigned assets
    # - Assets in manager's department
    #
    if current_user.get("role") == "MANAGER":

        #
        # Manager has no department
        #
        if not current_user.get(
            "department_id"
        ):
            query = query.filter(
                Asset.assigned_to_user_id
                == current_user.get("id")
            )

        #
        # Manager has department
        #
        else:
            query = query.filter(
                or_(
                    Asset.assigned_to_user_id
                    == current_user.get("id"),

                    Asset.department_id
                    == current_user.get(
                        "department_id"
                    )
                )
            )

    #
    # Normal User:
    # Only own assets
    #
    else:
        query = query.filter(
            Asset.assigned_to_user_id
            == current_user.get("id")
        )

    return (
        query
        .order_by(
            Asset.name.asc()
        )
        .all()
    )



import json

def create_maintenance_task(
    db: Session,
    asset_id: str,
    payload: CreateMaintenanceRequest,
    current_user: dict
):
    asset = (
        db.query(Asset)
        .filter(
            Asset.id == asset_id,
            Asset.client_id
            == current_user["client_id"],
            Asset.is_active == True
        )
        .first()
    )

    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Asset not found."
        )

    #
    # USER can only raise
    # maintenance for assigned assets
    #
    if current_user["role"] == "USER":
        if (
            asset.assigned_to_user_id
            != current_user["id"]
        ):
            raise HTTPException(
                status_code=403,
                detail=(
                    "You can only create "
                    "maintenance requests "
                    "for assets assigned "
                    "to you."
                )
            )

    #
    # Prevent duplicate active tasks
    #
    existing = (
        db.query(MaintenanceTask)
        .filter(
            MaintenanceTask.asset_id
            == asset.id,
            MaintenanceTask.status.in_([
                "pending_approval",
                "approved",
                "in_progress"
            ])
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail=(
                "An active maintenance "
                "request already exists "
                "for this asset."
            )
        )

    task = MaintenanceTask(
        asset_id=asset.id,
        client_id=asset.client_id,
        raised_by=current_user["id"],
        issue_description=
        payload.issue_description,
        photos_urls=json.dumps(
            payload.photos_urls
            or []
        ),
        estimated_cost=
        payload.estimated_cost,
        is_emergency=
        payload.is_emergency,
        vendor_name=
        payload.vendor_name,
        status="pending_approval"
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    return task
from datetime import datetime


def approve_maintenance(
    db: Session,
    maintenance_id: str,
    current_user: dict
):
    task = (
        db.query(MaintenanceTask)
        .filter(
            MaintenanceTask.id
            == maintenance_id
        )
        .first()
    )

    if not task:
        raise HTTPException(
            status_code=404,
            detail=
            "Maintenance task not found."
        )

    if (
        task.status
        != "pending_approval"
    ):
        raise HTTPException(
            status_code=400,
            detail=
            "Only pending requests can be approved."
        )

    task.status = "approved"
    task.approved_by = current_user["id"]
    task.approved_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(task)

    return task

def start_maintenance(
    db: Session,
    maintenance_id: str,
    current_user: dict

):
    task = (
        db.query(MaintenanceTask)
        .filter(
            MaintenanceTask.id
            == maintenance_id
        )
        .first()
    )
    print("++++++++++++++++++++++++==")
    print(task)
    print(maintenance_id)
    print(current_user)
    print("++++++++++++++++++++++++++")

    if not task:
        raise HTTPException(
            status_code=404,
            detail=
            "Maintenance task not found."
        )

    if (
        task.status
        != "approved"
    ):
        raise HTTPException(
            status_code=400,
            detail=
            "Maintenance request "
            "must be approved first."
        )

    task.status = "in_progress"
    task.started_at = datetime.now(timezone.utc)

    asset = (
        db.query(Asset)
        .filter(
            Asset.id
            == task.asset_id
        )
        .first()
    )

    if asset:
        asset.asset_condition = (
            "UNDER_MAINTENANCE"
        )

    db.commit()
    db.refresh(task)

    return task


def complete_maintenance(
    db: Session,
    maintenance_id: str,
    current_user: dict
):
    task = (
        db.query(MaintenanceTask)
        .filter(
            MaintenanceTask.id
            == maintenance_id
        )
        .first()
    )

    if not task:
        raise HTTPException(
            status_code=404,
            detail=
            "Maintenance task not found."
        )

    if (
        task.status
        != "in_progress"
    ):
        raise HTTPException(
            status_code=400,
            detail=
            "Maintenance task "
            "is not in progress."
        )

    task.status = "completed"
    task.completed_at = datetime.now(timezone.utc)

    asset = (
        db.query(Asset)
        .filter(
            Asset.id
            == task.asset_id
        )
        .first()
    )

    if asset:
        asset.asset_condition = "ACTIVE"

    db.commit()
    db.refresh(task)

    return task


def approve_maintenance(
    db: Session,
    maintenance_id: str,
    current_user: dict
):
    task = (
        db.query(
            MaintenanceTask
        )
        .filter(
            MaintenanceTask.id
            ==
            maintenance_id
        )
        .first()
    )

    if not task:
        raise HTTPException(
            status_code=404,
            detail=
            "Maintenance task not found."
        )

    if (
        task.status
        !=
        "pending_approval"
    ):
        raise HTTPException(
            status_code=400,
            detail=
            "Task cannot be approved."
        )

    task.status = "approved"
    task.approved_by = current_user["id"]

    db.commit()
    db.refresh(task)

    return task



def complete_maintenance(
    db: Session,
    maintenance_id: str
):
    task = (
        db.query(
            MaintenanceTask
        )
        .filter(
            MaintenanceTask.id
            ==
            maintenance_id
        )
        .first()
    )

    if not task:
        raise HTTPException(
            status_code=404,
            detail=
            "Maintenance task not found."
        )

    if (
        task.status
        !=
        "in_progress"
    ):
        raise HTTPException(
            status_code=400,
            detail=
            "Maintenance is not in progress."
        )

    task.status ="completed"

    task.completed_at = (
        datetime.utcnow()
    )

    asset = (
        db.query(Asset)
        .filter(
            Asset.id
            ==
            task.asset_id
        )
        .first()
    )

    if asset:
        asset.asset_condition = (
            "ACTIVE"
        )

    db.commit()
    db.refresh(task)

    return task




from datetime import datetime


def complete_maintenance(
    db: Session,
    maintenance_id: str,
    current_user: dict
):
    task = (
        db.query(MaintenanceTask)
        .filter(
            MaintenanceTask.id
            == maintenance_id
        )
        .first()
    )

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Maintenance task not found."
        )

    if (
        task.client_id
        != current_user["client_id"]
    ):
        raise HTTPException(
            status_code=403,
            detail="Access denied."
        )

    if (
        task.status
        != "in_progress"
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Maintenance task "
                "is not in progress."
            )
        )

    task.status = "completed"
    task.completed_at = (
        datetime.utcnow()
    )

    asset = (
        db.query(Asset)
        .filter(
            Asset.id
            == task.asset_id
        )
        .first()
    )

    if asset:
        asset.asset_condition = (
            "ACTIVE"
        )

    db.commit()
    db.refresh(task)

    return task



def reject_maintenance(
    db: Session,
    maintenance_id: str,
    payload: RejectMaintenanceRequest,
    current_user: dict
):
    task = (
        db.query(MaintenanceTask)
        .filter(
            MaintenanceTask.id
            == maintenance_id
        )
        .first()
    )

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Maintenance task not found."
        )

    if (
        task.client_id
        != current_user["client_id"]
    ):
        raise HTTPException(
            status_code=403,
            detail="Access denied."
        )

    if (
        task.status
        != "pending_approval"
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Only pending "
                "maintenance requests "
                "can be rejected."
            )
        )

    task.status = "rejected"
    task.rejection_reason = (
        payload.rejection_reason
    )

    db.commit()
    db.refresh(task)

    return task




def get_asset_maintenance(
    db: Session,
    asset_id: str,
    current_user: dict
):
    return (
        db.query(MaintenanceTask)
        .filter(
            MaintenanceTask.asset_id
            == asset_id,
            MaintenanceTask.client_id
            ==
            current_user["client_id"]
        )
        .order_by(
            MaintenanceTask.created_at
            .desc()
        )
        .all()
    )



def get_asset_maintenance(
    db: Session,
    asset_id: str,
    current_user: dict
):
    return (
        db.query(MaintenanceTask)
        .filter(
            MaintenanceTask.asset_id
            == asset_id,
            MaintenanceTask.client_id
            ==
            current_user["client_id"]
        )
        .order_by(
            MaintenanceTask.created_at
            .desc()
        )
        .all()
    )


def get_maintenance_tasks(
    db: Session,
    current_user: dict,
    status: str | None = None
):
    query = (
        db.query(MaintenanceTask)
    )

    #
    # Platform Admin
    # can see everything
    #
    if current_user["role"] != "ADMIN":
        query = query.filter(
            MaintenanceTask.client_id
            == current_user["client_id"]
        )

    #
    # Optional status filter
    #
    if status:
        query = query.filter(
            MaintenanceTask.status
            == status
        )

    return (
        query
        .order_by(
            MaintenanceTask.created_at.desc()
        )
        .all()
    )



from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.maintenance_task import MaintenanceTask


def get_maintenance_task(
    db: Session,
    maintenance_id: str,
    current_user: dict
):
    task = (
        db.query(MaintenanceTask)
        .filter(
            MaintenanceTask.id
            == maintenance_id
        )
        .first()
    )

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Maintenance task not found."
        )

    #
    # Platform Admin can access everything
    #
    if current_user["role"] != "ADMIN":
        if (
            task.client_id
            != current_user["client_id"]
        ):
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to view this maintenance task."
            )

    return task