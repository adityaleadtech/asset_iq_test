import json

from datetime import date, datetime
from typing import List, Optional, Literal, Annotated

from fastapi import (
    APIRouter,
    Depends,
    status,
    Query,
    HTTPException,
    UploadFile,
    File,
    Form
	
)

from sqlalchemy import (
    or_,
    and_,
    asc,
    desc,
    false
)

from sqlalchemy.orm import (
    Session,
    joinedload
)

from pydantic import (
    BaseModel,
    Field
)

from app.config.dependencies import get_db
from app.models.asset import Asset
from app.models.departments import Department
from app.models.location import Location
from app.utils.auth import client_admin_required, get_current_user
from app.config.permission import has_permission
from app.schemas.assets import (
    AssetBulkCreate,
    AssetCreate,
    AssetDashboardResponse,
    AssetLocationResponse,
    AssetTimelineItem,
    AssetUpdate,
    AssetResponse,
    AssetAssignRequest,
    AssetVerificationFormResponse,
    AssetVerificationRequest,
    AssetAuditResponse,
    AssetQrResponse,
    AssetConditionStatsResponse,
    AssetTaggingStatsResponse,
    CreateMaintenanceRequest,
    MaintenanceTaskResponse,
    MarkLostRequest,
    RejectMaintenanceRequest,
)
from app.services import assets as asset_service
from app.services.assets import (
    approve_maintenance,
    bulk_create_assets,
    complete_maintenance,
    create_maintenance_task,
    get_asset_audits,
    get_asset_dashboard,
    get_asset_location,
    get_asset_maintenance,
    get_asset_verification_data,
    get_asset_qr,
    get_maintenance_tasks,
    get_my_assets,
    regenerate_asset_qr,
    reject_maintenance,
    search_assets,
    get_asset_condition_stats,
    get_asset_tagging_stats,
    start_maintenance,
    get_maintenance_task,
)
from app.schemas.transfers import (
    AssetTransferRequest,
    TransferHistoryResponse
)
from app.services.transfers import transfer_asset

router = APIRouter(prefix="/assets", tags=["Assets"])

# ==================== HELPER DEPENDENCY ====================
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

# ==================== LITERAL TYPES ====================
AssetConditionLiteral = Literal[
    "ACTIVE",
    "INACTIVE", 
    "DAMAGED",
    "UNDER_MAINTENANCE",
    "LOST"
]

TagStateLiteral = Literal[
    "TAGGED",
    "NOT_TAGGED"
]

SortByLiteral = Literal[
    "name",
    "manufacturer",
    "purchase_date",
    "created_at",
    "serial_number",
    "asset_condition",
    "tag_state",
    "last_scanned_at",
    "model"
]

SortOrderLiteral = Literal[
    "asc",
    "desc"
]

# ==================== PAGINATION MODELS ====================
class PaginationMeta(BaseModel):
    page: int = Field(..., example=1, description="Current page number")
    limit: int = Field(..., example=20, description="Items per page")
    total: int = Field(..., example=150, description="Total matching items")
    total_pages: int = Field(..., example=8, description="Total pages")
    has_next: bool = Field(..., example=True, description="Has next page")
    has_previous: bool = Field(..., example=False, description="Has previous page")

class AssetSearchResponse(BaseModel):
    items: List[AssetResponse] = Field(..., description="List of matching assets")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")

# ==================== DASHBOARD & ANALYTICS ====================
@router.get(
    "/dashboard",
    response_model=AssetDashboardResponse,
    summary="Asset Dashboard Role based",
    description="Get asset dashboard analytics and statistics. Client admin can see their own assets, User with asset_management can see their own assets(Client) platform admin can see all assets with no query parameters and with query parameters they can see specific clients assets "
)
def fetch_asset_dashboard(
    client_id: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(check_permission("ASSET_MANAGEMENT", "read"))
):
    return get_asset_dashboard(db, current_user, client_id)

# ==================== SEARCH (MUST COME BEFORE /{asset_id}) ====================
@router.get(
    "/search",
    response_model=AssetSearchResponse,
    summary="Search Assets",
    description="search assets based on various filters and search terms. The results are paginated and sorted based on the provided parameters."
)
def search_assets_endpoint(
    current_user: dict = Depends(check_permission("ASSET_MANAGEMENT", "read")),
    db: Session = Depends(get_db),
    q: Optional[str] = Query(None, description="Search query", min_length=1, max_length=100),
    client_id: Optional[str] = Query(None, description="Filter by client ID"),
    category_id: Optional[str] = Query(None, description="Filter by category ID"),
    type_id: Optional[str] = Query(None, description="Filter by type ID"),
    department_id: Optional[str] = Query(None, description="Filter by department ID"),
    location_id: Optional[str] = Query(None, description="Filter by location ID"),
    assigned_to_user_id: Optional[str] = Query(None, description="Filter by assigned user ID"),
    asset_condition: Optional[AssetConditionLiteral] = Query(None, description="Filter by asset condition"),
    tag_state: Optional[TagStateLiteral] = Query(None, description="Filter by tag state"),
    manufacturer: Optional[str] = Query(None, description="Filter by manufacturer"),
    serial_number: Optional[str] = Query(None, description="Filter by serial number"),
    created_by: Optional[str] = Query(None, description="Filter by creator user ID"),
    purchase_start_date: Optional[date] = Query(None, description="Purchase date greater than or equal"),
    purchase_end_date: Optional[date] = Query(None, description="Purchase date less than or equal"),
    last_scanned_from: Optional[datetime] = Query(None, description="Last scanned date from"),
    last_scanned_to: Optional[datetime] = Query(None, description="Last scanned date to"),
    sort_by: SortByLiteral = Query("created_at", description="Sort field"),
    sort_order: SortOrderLiteral = Query("desc", description="Sort order"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page")
):
    if client_id and current_user["role"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Only platform administrators can filter by client_id")
    if created_by and current_user["role"] not in ["ADMIN", "CLIENT_ADMIN"]:
        raise HTTPException(status_code=403, detail="Only ADMIN or CLIENT_ADMIN can filter by creator")
    if purchase_start_date and purchase_end_date and purchase_start_date > purchase_end_date:
        raise HTTPException(status_code=400, detail="purchase_start_date cannot be greater than purchase_end_date")
    if last_scanned_from and last_scanned_to and last_scanned_from > last_scanned_to:
        raise HTTPException(status_code=400, detail="last_scanned_from cannot be greater than last_scanned_to")
    
    result = search_assets(
        db=db, current_user=current_user, q=q, client_id=client_id,
        category_id=category_id, type_id=type_id, department_id=department_id,
        location_id=location_id, assigned_to_user_id=assigned_to_user_id,
        asset_condition=asset_condition, tag_state=tag_state,
        manufacturer=manufacturer, serial_number=serial_number,
        created_by=created_by, purchase_start_date=purchase_start_date,
        purchase_end_date=purchase_end_date, last_scanned_from=last_scanned_from,
        last_scanned_to=last_scanned_to, sort_by=sort_by,
        sort_order=sort_order, page=page, limit=limit
    )
    return result

# ==================== STATISTICS (MUST COME BEFORE /{asset_id}) ====================
@router.get(
    "/stats/conditions",
    response_model=AssetConditionStatsResponse,
    summary="Fetch Asset Condition Statistics",
    description="fetch stats of assets conditions like \nACTIVE,\nINACTIVE,\nDAMAGED,\nUNDER_MAINTENANCE,\nLOST based on the client of the current user. Platform admin can pass client_id as query parameter to get stats of specific client"
)
def fetch_asset_condition_stats(
    client_id: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(check_permission("ASSET_MANAGEMENT", "read"))
):
    return get_asset_condition_stats(db, current_user, client_id)

@router.get(
    "/stats/tagging",
    response_model=AssetTaggingStatsResponse,
    summary="Fetch Asset Tagging Statistics",
    description="Tagging stats of assets are \n-TAGGED or \n-NOT_TAGGED \nbased on the client of the current user. Platform admin can pass client_id as query parameter to get stats of specific client"
)
def fetch_asset_tagging_stats(
    client_id: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(check_permission("ASSET_MANAGEMENT", "read"))
):
    return get_asset_tagging_stats(db, current_user, client_id)

# ==================== BULK OPERATIONS (MUST COME BEFORE /{asset_id}) ====================
@router.post(
    "/bulk",
    status_code=status.HTTP_201_CREATED,
    summary="Bulk Create Assets",
    description="""
Bulk create multiple assets in a single request.

The API automatically determines the target client based on the
authenticated user's role.

ADMIN / Platform Admin:
- Must provide client_id in the request body.
- Assets are created for the specified client.

CLIENT_ADMIN:
- client_id is automatically read from the JWT token.
- Any client_id provided in the request body is ignored.

MANAGER or Custom Role:
- Must have ASSET_MANAGEMENT.create permission.
- client_id is automatically read from the JWT token.

All assets in one bulk request are created for the same client.

Example ADMIN request:

{
    "client_id": "CLIENT_UUID",
    "assets": [
        {
            "category_id": "CATEGORY_UUID",
            "type_id": "TYPE_UUID",
            "name": "Dell Laptop 1",
            "department_id": "DEPARTMENT_UUID",
            "location_id": "LOCATION_UUID",
            "serial_number": "DELL-001",
            "model": "Latitude 5420",
            "manufacturer": "Dell",
            "purchase_date": "2026-07-04",
            "purchase_value": 65000,
            "custom_fields": []
        },
        {
            "category_id": "CATEGORY_UUID",
            "type_id": "TYPE_UUID",
            "name": "Dell Laptop 2",
            "serial_number": "DELL-002",
            "custom_fields": []
        }
    ]
}

For CLIENT_ADMIN, MANAGER, or a custom role:

{
    "assets": [
        {
            "category_id": "CATEGORY_UUID",
            "type_id": "TYPE_UUID",
            "name": "Dell Laptop 1",
            "custom_fields": []
        }
    ]
}
"""
)
def create_assets_bulk(
    payload: AssetBulkCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        check_permission(
            "ASSET_MANAGEMENT",
            "create"
        )
    )
):

    # =====================================
    # Resolve Current User Role
    # =====================================

    role = str(
        current_user.get(
            "role",
            ""
        )
    ).upper()

    # =====================================
    # Platform Admin
    # =====================================

    if role == "ADMIN":

        if not payload.client_id:

            raise HTTPException(
                status_code=400,
                detail=(
                    "client_id is required "
                    "for Platform Admin"
                )
            )

        client_id = payload.client_id

    # =====================================
    # Client Users
    # =====================================

    else:

        client_id = current_user.get(
            "client_id"
        )

        if not client_id:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Authenticated user is not "
                    "associated with a client"
                )
            )

    # =====================================
    # Bulk Create Assets
    # =====================================

    return bulk_create_assets(
        db=db,
        payload=payload,
        client_id=client_id,
        created_by=current_user["id"]
    )

# ==================== MY ASSETS (MUST COME BEFORE /{asset_id}) ====================
#to fix Platform admin to see specific user's asset
@router.get(
    "/my-assets",
    response_model=list[AssetResponse],
    summary="Get My Assets",
    description="""
Returns assets visible to the current user.

USER:
- Assets assigned to the user.

MANAGER:
- Assets assigned to the manager.
- Assets belonging to the manager's department.
PLATFORM ADMIN
- Can see all assets, but must provide user_id query parameter to see specific user's assets.   
"""
)
def get_my_assets_router(
    db: Session = Depends(get_db),
    current_user=Depends(
        check_permission(
            "ASSET_MANAGEMENT",
            "read"
        )
    ),
    user_id: str | None = None
):
    print("______________________________________________________________________________________________________________________________"+str(current_user.get("role")))
    if current_user.get("role") == "ADMIN":
        if not user_id:
            raise HTTPException(
                status_code=400,
                detail="user_id is required for platform admin"
            )
        
        
    return get_my_assets(
        db,
        current_user,
        user_id
    )

# ==================== MAINTENANCE TASKS (MUST COME BEFORE /{asset_id}) ====================
@router.get(
    "/maintenance",
    response_model=list[MaintenanceTaskResponse],
    summary="Get Maintenance Tasks",
    description="""
Fetch maintenance tasks.

Query Parameter:
- pending_approval
- approved
- in_progress
- completed

Only users with ASSET_MANAGEMENT.update permission
can access this endpoint.
"""
)
def get_maintenance_tasks_router(
    status: str | None = Query(
        default=None,
        description=(
            "Filter maintenance tasks by status.\n\n"
            "Available values:\n"
            "- pending_approval\n"
            "- approved\n"
            "- in_progress\n"
            "- completed"
        )
    ),
    db: Session = Depends(get_db),
    current_user=Depends(
        check_permission(
            "ASSET_MANAGEMENT",
            "update"
        )
    )
):
    return (
        get_maintenance_tasks(
            db,
            current_user,
            status
        )
    )

@router.get(
    "/maintenance/{maintenance_id}",
    response_model=MaintenanceTaskResponse,
    summary="Get Maintenance Task By ID"
)
def get_maintenance_task_router(
    maintenance_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
        check_permission(
            "ASSET_MANAGEMENT",
            "read"
        )
    )
):
    return (
        get_maintenance_task(
            db,
            maintenance_id,
            current_user
        )
    )

@router.patch(
    "/maintenance/{maintenance_id}/approve",
    response_model=MaintenanceTaskResponse,
    summary="Approve Maintenance"
)
def approve_maintenance_task(
    maintenance_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
        check_permission(
            "ASSET_MANAGEMENT",
            "update"
        )
    )
):
    return (
        approve_maintenance(
            db,
            maintenance_id,
            current_user
        )
    )

@router.patch(
    "/maintenance/{maintenance_id}/start",
    response_model=MaintenanceTaskResponse,
    summary="Start Maintenance"
)
def start_maintenance_task(
    maintenance_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
        check_permission(
            "ASSET_MANAGEMENT",
            "update"
        )
    )
):
    return (
        start_maintenance(
            db,
            maintenance_id,
            current_user
        )
    )

@router.patch(
    "/maintenance/{maintenance_id}/complete",
    response_model=MaintenanceTaskResponse,
    summary="Complete Maintenance"
)
def complete_maintenance_task(
    maintenance_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
        check_permission(
            "ASSET_MANAGEMENT",
            "update"
        )
    )
):
    return (
        complete_maintenance(
            db,
            maintenance_id,
            current_user
        )
    )

@router.patch(
    "/maintenance/{maintenance_id}/reject",
    response_model=MaintenanceTaskResponse,
    summary="Reject Maintenance"
)
def reject_maintenance_task(
    maintenance_id: str,
    payload: RejectMaintenanceRequest,
    db: Session = Depends(get_db),
    current_user=Depends(
        check_permission(
            "ASSET_MANAGEMENT",
            "update"
        )
    )
):
    return (
        reject_maintenance(
            db,
            maintenance_id,
            payload,
            current_user
        )
    )

# ==================== ASSET-SPECIFIC MAINTENANCE (MUST COME BEFORE /{asset_id}) ====================
@router.post(
    "/{asset_id}/maintenance",
    response_model=MaintenanceTaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Maintenance Request",
    description="""
Create a maintenance request.

Permissions:

USER
- Can create requests only
  for assets assigned to them.

MANAGER
- Can create requests for
  accessible assets.

CLIENT_ADMIN
- Can create requests for any
  asset in their client.

ADMIN
- Can create requests for any
  asset.
"""
)
def create_asset_maintenance(
    asset_id: str,
    payload: CreateMaintenanceRequest,
    db: Session = Depends(get_db),
    current_user=Depends(
        check_permission(
            "ASSET_MANAGEMENT",
            "update"
        )
    )
):
    return (
        create_maintenance_task(
            db,
            asset_id,
            payload,
            current_user
        )
    )

@router.get(
    "/{asset_id}/maintenance",
    response_model=list[MaintenanceTaskResponse],
    summary="Get Maintenance History For Asset"
)
def get_asset_maintenance_router(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
        check_permission(
            "ASSET_MANAGEMENT",
            "read"
        )
    )
):
    return (
        get_asset_maintenance(
            db,
            asset_id,
            current_user
        )
    )

# ==================== ASSET OPERATIONS (MUST COME BEFORE /{asset_id}) ====================
@router.post(
    "/{asset_id}/transfer",
    response_model=AssetResponse,
    summary="Transfer Asset"
)
def transfer_existing_asset(
    asset_id: str,
    payload: AssetTransferRequest,
    db: Session = Depends(get_db),
    current_user=Depends(check_permission("ASSET_MANAGEMENT", "update"))
):
    return transfer_asset(db, asset_id, payload, current_user)

@router.get(
    "/{asset_id}/transfers",
    response_model=list[TransferHistoryResponse],
    summary="Fetch Asset Transfer History"
)
def fetch_asset_transfers(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(check_permission("ASSET_MANAGEMENT", "read"))
):
    return asset_service.get_asset_transfers(db, asset_id, current_user)

@router.post(
    "/{asset_id}/mark-lost",
    response_model=AssetResponse,
    summary="Mark Asset as Lost"
)
def mark_lost_asset(
    asset_id: str,
    payload: MarkLostRequest,
    db: Session = Depends(get_db),
    current_user=Depends(check_permission("ASSET_MANAGEMENT", "update"))
):
    return asset_service.mark_asset_lost(db, asset_id, payload, current_user)

@router.get(
    "/{asset_id}/timeline",
    response_model=list[AssetTimelineItem],
    summary="Fetch Asset Timeline"
)
def fetch_asset_timeline(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(check_permission("ASSET_MANAGEMENT", "read"))
):
    return asset_service.get_asset_timeline(db, asset_id, current_user)

@router.post(
    "/{asset_id}/assign",
    response_model=AssetResponse,
    status_code=status.HTTP_200_OK,
    summary="Assign asset to a user"
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
    summary="Unassign an asset"
)
def unassign_existing_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(check_permission("ASSET_MANAGEMENT", "update"))
):
    return asset_service.unassign_asset(db, asset_id, current_user)

@router.get(
    "/{asset_id}/qr",
    response_model=AssetQrResponse,
    summary="Fetch Asset QR Code"
)
def fetch_asset_qr(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(check_permission("ASSET_MANAGEMENT", "read"))
):
    return get_asset_qr(db, asset_id, current_user)

@router.post(
    "/{asset_id}/regenerate-qr",
    response_model=AssetQrResponse,
    summary="Regenerate Asset QR Code"
)
def regenerate_qr(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(check_permission("ASSET_MANAGEMENT", "update"))
):
    return regenerate_asset_qr(db, asset_id, current_user)

@router.get(
    "/{asset_id}/audits",
    response_model=list[AssetAuditResponse],
    summary="Fetch Asset Audit History"
)
def fetch_asset_audits(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return get_asset_audits(db, asset_id, current_user)

@router.get(
    "/{asset_id}/location",
    response_model=AssetLocationResponse,
    summary="Fetch Asset Location"
)
def fetch_asset_location(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return get_asset_location(db, asset_id, current_user)

@router.get(
    "/verify/{asset_id}",
    response_model=AssetVerificationFormResponse,
    summary="Fetch Verification Form Data"
)
def fetch_verification_data(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(check_permission("ASSET_MANAGEMENT", "read"))
):
    return get_asset_verification_data(db, asset_id, current_user)

from fastapi import Form, File, UploadFile
from fastapi import Form, File, UploadFile

@router.post(
    "/{asset_id}/verify",
    response_model=AssetResponse,
    summary="Verify Asset"
)
async def verify_existing_asset(  # Make it async
    asset_id: str,
    latitude: float = Form(...),
    longitude: float = Form(...),
    asset_condition: str = Form(...),
    remarks: str | None = Form(None),
    image_file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    verification_data = AssetVerificationRequest(
        latitude=latitude,
        longitude=longitude,
        asset_condition=asset_condition,
        remarks=remarks,
        image_url=None
    )
    
    return await asset_service.verify_asset(  # await the result
        db, 
        asset_id, 
        verification_data, 
        image_file, 
        current_user
    )
# ==================== GENERIC ASSET CRUD (MUST COME LAST) ====================
# These catch-all routes must be defined LAST

@router.get(
    "",
    response_model=list[AssetResponse],
    summary="Fetch all assets"
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
Create an asset with an image.

Request type:

multipart/form-data

Fields:

asset_data:
JSON string containing asset information.

image_file:
Asset image file.
"""
)
def create_new_asset(
    asset_data: str = Form(...),
    image_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(
        check_permission(
            "ASSET_MANAGEMENT",
            "create"
        )
    )
):

    # =====================================
    # Parse JSON
    # =====================================

    try:

        parsed_asset_data = json.loads(
            asset_data
        )

    except json.JSONDecodeError as error:

        raise HTTPException(
            status_code=422,
            detail={
                "message": (
                    "asset_data must be valid JSON"
                ),
                "error": str(error)
            }
        )

    # =====================================
    # Validate Schema
    # =====================================

    try:

        validated_asset_data = (
            AssetCreate(
                **parsed_asset_data
            )
        )

    except ValidationError as error:

        raise HTTPException(
            status_code=422,
            detail=error.errors()
        )

    # =====================================
    # Create Asset
    # =====================================

    return asset_service.create_asset(
        db=db,
        asset_data=validated_asset_data,
        current_user=current_user,
        image_file=image_file
    )
@router.get(
    "/{asset_id}",  # This catches ANYTHING - must be ABSOLUTELY LAST!
    response_model=AssetResponse,
    summary="Fetch asset by ID"
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
    summary="Update an asset"
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
    summary="Delete an asset"
)
def delete_existing_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(check_permission("ASSET_MANAGEMENT", "delete"))
):
    return asset_service.deactivate_asset(db, asset_id, current_user)

# ==================== SEARCH SERVICE ====================
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
    asset_condition: Optional[AssetConditionLiteral] = None,
    tag_state: Optional[TagStateLiteral] = None,
    manufacturer: Optional[str] = None,
    serial_number: Optional[str] = None,
    purchase_start_date: Optional[date] = None,
    purchase_end_date: Optional[date] = None,
    last_scanned_from: Optional[datetime] = None,
    last_scanned_to: Optional[datetime] = None,
    created_by: Optional[str] = None,
    sort_by: SortByLiteral = "created_at",
    sort_order: SortOrderLiteral = "desc",
    page: int = 1,
    limit: int = 20
):
    """Core asset search logic with role-based access control."""
    
    query = (
        db.query(Asset)
        .filter(Asset.is_active == True)
        .options(
            joinedload(Asset.category),
            joinedload(Asset.asset_type),
            joinedload(Asset.department),
            joinedload(Asset.location),
            joinedload(Asset.assigned_to_user)
        )
    )

    user_role = current_user.get("role")
    
    if user_role == "ADMIN":
        if client_id:
            query = query.filter(Asset.client_id == client_id)
    else:
        query = query.filter(Asset.client_id == current_user["client_id"])
        
        if user_role == "MANAGER":
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
                query = query.filter(false())
            else:
                query = query.filter(Asset.department_id.in_(department_ids))
        elif user_role == "USER" and not current_user.get("custom_role_id"):
            query = query.filter(Asset.assigned_to_user_id == current_user["id"])

    if q:
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
                    Location.name.ilike(f"%{term}%"),
                    Location.code.ilike(f"%{term}%"),
                    Location.address.ilike(f"%{term}%")
                )
            )
        if search_filters:
            query = query.filter(and_(*search_filters))

    if category_id:
        query = query.filter(Asset.category_id == category_id)
    if type_id:
        query = query.filter(Asset.type_id == type_id)
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
    if created_by:
        query = query.filter(Asset.created_by == created_by)
    if manufacturer:
        query = query.filter(Asset.manufacturer.ilike(f"%{manufacturer}%"))
    if serial_number:
        query = query.filter(Asset.serial_number == serial_number)
    if purchase_start_date:
        query = query.filter(Asset.purchase_date >= purchase_start_date)
    if purchase_end_date:
        query = query.filter(Asset.purchase_date <= purchase_end_date)
    if last_scanned_from:
        query = query.filter(Asset.last_scanned_at >= last_scanned_from)
    if last_scanned_to:
        query = query.filter(Asset.last_scanned_at <= last_scanned_to)

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
    }
    sort_column = sortable_fields[sort_by]
    
    if sort_order == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column), desc(Asset.created_at))

    total = query.distinct(Asset.id).count()
    assets = (
        query
        .distinct(Asset.id)
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    total_pages = (total + limit - 1) // limit

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