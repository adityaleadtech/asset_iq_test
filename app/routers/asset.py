from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.config.dependencies import get_db
from app.utils.auth import get_current_user
from app.config.permission import has_permission
from app.schemas.assets import (
    AssetCreate,
    AssetLocationResponse,
    AssetUpdate,
    AssetResponse,
    AssetAssignRequest,
    AssetVerificationFormResponse,
    AssetVerificationRequest,
)
from app.services import assets as asset_service

router = APIRouter(prefix="/assets", tags=["Assets"])


# Create a wrapper function that includes db
def check_permission(service_code: str, action: str):
    def dependency(
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user)
    ):
        if not has_permission(db, current_user, service_code, action):
            from fastapi import HTTPException
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: {service_code}.{action}"
            )
        return current_user
    return dependency


@router.get(
    "",
    response_model=list[AssetResponse],
    summary="Fetch all assets",
    description="""
    Fetch all assets based on user role.
    
    **Access:**
    - **ADMIN** → Can view all assets across all clients
    - **CLIENT_ADMIN** → Can view all assets belonging to their client
    - **MANAGER** → Can view assets belonging to departments they manage
    - **CUSTOM ROLE** → Can view all assets belonging to their client (requires ASSET_MANAGEMENT.read permission)
    - **USER** → Can view only assets assigned to them
    """
)
def fetch_assets(
    db: Session = Depends(get_db),
    current_user=Depends(check_permission("ASSET_MANAGEMENT", "read"))
):
    return asset_service.get_assets(db, current_user)


@router.post(
    "",
    response_model=AssetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new asset",
    description="""
    Create a new asset.
    
    **Access:**
    - **ADMIN** → Can create assets for any client (must specify client_id)
    - **CLIENT_ADMIN** → Can create assets for their client
    - **MANAGER** → Can create assets inside departments they manage
    - **CUSTOM ROLE** → Requires ASSET_MANAGEMENT.create permission
    
    **Validation:**
    - Active subscription required
    - Asset limit not exceeded
    - Serial number uniqueness
    - Category and type must belong to client (or be global)
    - Type must belong to selected category
    - Department must exist
    - Assigned user (if provided) must exist and belong to client
    
    **QR Generation:**
    - QR code is automatically generated and uploaded to Cloudinary
    - QR generation failure does not block asset creation
    """
)
def create_new_asset(
    asset_data: AssetCreate,
    db: Session = Depends(get_db),
    current_user=Depends(check_permission("ASSET_MANAGEMENT", "create"))
):
    return asset_service.create_asset(db, asset_data, current_user)


@router.get(
    "/{asset_id}",
    response_model=AssetResponse,
    summary="Fetch asset by ID",
    description="""
    Fetch a specific asset by its ID.
    
    **Access:**
    - **ADMIN** → Can view any asset
    - **CLIENT_ADMIN** → Can view any asset in their client
    - **MANAGER** → Can view assets in managed departments only
    - **CUSTOM ROLE** → Can view any asset in their client (requires ASSET_MANAGEMENT.read permission)
    - **USER** → Can view only assets assigned to them
    """
)
def fetch_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(check_permission("ASSET_MANAGEMENT", "read"))
):
    return asset_service.get_asset_by_id(db, asset_id, current_user)


@router.patch(
    "/{asset_id}",
    response_model=AssetResponse,
    summary="Update an asset",
    description="""
    Update an existing asset.
    
    **Access:**
    - **ADMIN** → Can update any asset
    - **CLIENT_ADMIN** → Can update any asset in their client
    - **MANAGER** → Can update assets in managed departments only
    - **CUSTOM ROLE** → Requires ASSET_MANAGEMENT.update permission
    
    **Validation:**
    - Asset must exist
    - Category and type must belong to client (or be global)
    - Department must exist
    - Assigned user (if provided) must exist
    - Serial number uniqueness (if updated)
    - Type must belong to selected category
    """
)
def update_existing_asset(
    asset_id: str,
    asset_data: AssetUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(check_permission("ASSET_MANAGEMENT", "update"))
):
    return asset_service.update_asset(db, asset_id, asset_data, current_user)


@router.delete(
    "/{asset_id}",
    response_model=AssetResponse,
    summary="Delete an asset",
    description="""
    Soft delete an asset (set is_active = False).
    
    **Access:**
    - **ADMIN** → Can delete any asset
    - **CLIENT_ADMIN** → Can delete any asset in their client
    - **MANAGER** → Can delete assets in managed departments only
    - **CUSTOM ROLE** → Requires ASSET_MANAGEMENT.delete permission
    
    **Note:**
    - This is a soft delete - asset remains in database with is_active = False
    - Asset can be restored by setting is_active = True
    - Returns the updated asset object
    """
)
def delete_existing_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(check_permission("ASSET_MANAGEMENT", "delete"))
):
    return asset_service.deactivate_asset(db, asset_id, current_user)


@router.post(
    "/{asset_id}/assign",
    response_model=AssetResponse,
    status_code=status.HTTP_200_OK,
    summary="Assign asset to a user",
    description="""
    Assign an asset to a user.
    
    **Access:**
    - **ADMIN** → Can assign any asset to any user
    - **CLIENT_ADMIN** → Can assign any asset in their client
    - **MANAGER** → Can only assign assets inside departments they manage
    - **CUSTOM ROLE** → Requires ASSET_MANAGEMENT.update permission
    
    **Validation:**
    - Asset must exist
    - User must exist
    - User must belong to same client
    - Managers can only assign assets inside departments they manage
    - CLIENT_ADMIN and Custom Roles may assign assets across departments
    - Asset cannot be assigned to a user it's already assigned to
    """
)
def assign_existing_asset(
    asset_id: str,
    request: AssetAssignRequest,
    db: Session = Depends(get_db),
    current_user=Depends(check_permission("ASSET_MANAGEMENT", "update"))
):
    return asset_service.assign_asset(db, asset_id, request.user_id, current_user)


@router.post(
    "/{asset_id}/unassign",
    response_model=AssetResponse,
    status_code=status.HTTP_200_OK,
    summary="Unassign an asset",
    description="""
    Remove the current assignment from an asset.
    
    **Access:**
    - **ADMIN** → Can unassign any asset
    - **CLIENT_ADMIN** → Can unassign any asset in their client
    - **MANAGER** → Can only unassign assets from departments they manage
    - **CUSTOM ROLE** → Requires ASSET_MANAGEMENT.update permission
    
    **Behaviour:**
    - assigned_to_user_id = null
    - status = AVAILABLE
    
    **Validation:**
    - Asset must exist
    - Asset must be currently assigned
    - Managers can only unassign assets from departments they manage
    """
)
def unassign_existing_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(check_permission("ASSET_MANAGEMENT", "update"))
):
    return asset_service.unassign_asset(db, asset_id, current_user)



@router.post(
    "/{asset_id}/verify",
    response_model=AssetResponse,
    summary="Verify Asset"
)
def verify_existing_asset(
    asset_id: str,
    verification_data: AssetVerificationRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return asset_service.verify_asset(
        db,
        asset_id,
        verification_data,
        current_user
    )


from app.schemas.assets import AssetAuditResponse
from app.services.assets import get_asset_audits, get_asset_location, get_asset_verification_data
from app.config.dependencies import get_db, get_current_user
from sqlalchemy.orm import Session
from fastapi import Depends


@router.get(
    "/{asset_id}/audits",
    response_model=list[AssetAuditResponse],
    summary="Fetch Asset Audit History",
    description="""
    Fetch complete verification and scan history of an asset.

    Access:
    - ADMIN → Any asset
    - CLIENT_ADMIN → Assets of their client
    - MANAGER → Assets in departments they manage
    - USER with ASSET_MANAGEMENT.read → All client assets
    - Normal USER → Only assets assigned to them

    Returns:
    - Scan location
    - Scan images
    - Asset condition at time of scan
    - Remarks
    - Scanner details
    - Scan timestamp
    """
)
def fetch_asset_audits(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return get_asset_audits(
        db,
        asset_id,
        current_user
    )


@router.get(
    "/verify/{asset_id}",
    response_model=AssetVerificationFormResponse,
    summary="Fetch Verification Form Data to be used with flutter when the scans the QR after the response this should be called"
)
def fetch_verification_data(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return asset_service.get_asset_verification_data(
        db,
        asset_id,
        current_user
    )


@router.get(
    "/verify/{asset_id}",
    response_model=AssetVerificationFormResponse,
    summary="Fetch Verification Form Data",
    description="""
    Returns prefilled asset information after QR scan.

    Access:
    - ADMIN
    - CLIENT_ADMIN
    - MANAGER
    - USER with ASSET_MANAGEMENT.read
    - Normal USER for assigned assets

    Used by Flutter after QR scanning.
    """
)
def fetch_verification_data(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return get_asset_verification_data(
        db,
        asset_id,
        current_user
        
    )



@router.get(
    "/{asset_id}/location",
    response_model=AssetLocationResponse,
    summary="Fetch Asset Location",
    description="""
    Fetch latest asset location.

    Access:
    - ADMIN
    - CLIENT_ADMIN
    - MANAGER
    - USER with ASSET_MANAGEMENT.read
    - Normal USER for assigned assets only

    Used by Flutter to display asset on map.
    """
)
def fetch_asset_location(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return get_asset_location(
        db,
        asset_id,
        current_user
    )



from app.schemas.assets import AssetQrResponse
from app.services.assets import get_asset_qr


@router.get(
    "/{asset_id}/qr",
    response_model=AssetQrResponse,
    summary="Fetch Asset QR",
    description="""
    Fetch QR code of an asset.

    Access:
    - ADMIN
    - CLIENT_ADMIN
    - MANAGER
    - USER with ASSET_MANAGEMENT.read
    - Normal USER for assigned assets only

    Used for:
    - View QR
    - Download QR
    - Print QR sticker
    - Share QR in Flutter
    """
)
def fetch_asset_qr(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
        check_permission(
            "ASSET_MANAGEMENT",
            "read"
        )
    )
):
    return get_asset_qr(
        db,
        asset_id,
        current_user
    )



from app.services.assets import (
    regenerate_asset_qr
)

@router.post(
    "/{asset_id}/regenerate-qr",
    response_model=AssetQrResponse,
    summary="Regenerate Asset QR",
    description="""
    Generate a fresh QR code for an asset.

    Access:
    - ADMIN
    - CLIENT_ADMIN
    - MANAGER
    - USER with ASSET_MANAGEMENT.update permission

    Used for:
    - Damaged QR stickers
    - Lost QR images
    - Reprinting labels
    - Fresh QR generation
    """
)
def regenerate_qr(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
        check_permission(
            "ASSET_MANAGEMENT",
            "update"
        )
    )
):
    return regenerate_asset_qr(
        db,
        asset_id,
        current_user
    )