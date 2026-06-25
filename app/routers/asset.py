from datetime import date, datetime
from typing import List, Optional, Literal
from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy import or_, and_, asc, desc, false
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel, Field

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
    # AssetSearchResponse,  # ❌ Remove this - we'll define it locally
    AssetUpdate,
    AssetResponse,  # ✅ Keep this
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
)
from app.services import assets as asset_service
from app.services.assets import (
    bulk_create_assets,
    get_asset_audits,
    get_asset_dashboard,
    get_asset_location,
    get_asset_verification_data,
    get_asset_qr,
    regenerate_asset_qr,
    search_assets,
    get_asset_condition_stats,
    get_asset_tagging_stats,
)

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
    summary="Asset Dashboard",
    description="Get asset dashboard analytics and statistics."
)
def fetch_asset_dashboard(
    client_id: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(check_permission("ASSET_MANAGEMENT", "read"))
):
    return get_asset_dashboard(db, current_user, client_id)

# ==================== ASSET MANAGEMENT (CRUD) ====================
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

@router.get(
    "/{asset_id}",
    response_model=AssetResponse,
    summary="Fetch asset by ID"
)
def fetch_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(check_permission("ASSET_MANAGEMENT", "read"))
):
    return asset_service.get_asset_by_id(db, asset_id, current_user)

@router.post(
    "",
    response_model=AssetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new asset"
)
def create_new_asset(
    asset_data: AssetCreate,
    db: Session = Depends(get_db),
    current_user=Depends(check_permission("ASSET_MANAGEMENT", "create"))
):
    return asset_service.create_asset(db, asset_data, current_user)

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

# ==================== ASSET ASSIGNMENT ====================
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

# ==================== QR CODE OPERATIONS ====================
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

# ==================== ASSET VERIFICATION ====================
@router.get(
    "/verify/{asset_id}",
    response_model=AssetVerificationFormResponse,
    summary="Fetch Verification Form Data"
)
def fetch_verification_data(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return get_asset_verification_data(db, asset_id, current_user)

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
    return asset_service.verify_asset(db, asset_id, verification_data, current_user)

# ==================== ASSET AUDIT & LOCATION ====================
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

# ==================== BULK OPERATIONS ====================
@router.post(
    "/bulk",
    status_code=status.HTTP_201_CREATED,
    summary="Bulk Create Assets"
)
def create_assets_bulk(
    payload: AssetBulkCreate,
    db: Session = Depends(get_db),
    current_user=Depends(client_admin_required)
):
    return bulk_create_assets(
        db=db,
        payload=payload,
        client_id=current_user["client_id"],
        created_by=current_user["id"]
    )

# ==================== STATISTICS ====================
@router.get(
    "/stats/conditions",
    response_model=AssetConditionStatsResponse,
    summary="Fetch Asset Condition Statistics"
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
    summary="Fetch Asset Tagging Statistics"
)
def fetch_asset_tagging_stats(
    client_id: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(check_permission("ASSET_MANAGEMENT", "read"))
):
    return get_asset_tagging_stats(db, current_user, client_id)

# ==================== SEARCH ENDPOINT ====================
@router.get(
    "/search",
    response_model=AssetSearchResponse,
    summary="Search Assets",
    description="""
    Search assets using one or more filters with advanced filtering, sorting, and pagination.

    ## Access Control
    - **ADMIN**: Can search across all clients with optional `client_id` filter
    - **CLIENT_ADMIN**: Can search within their client
    - **MANAGER**: Can search assets within departments they manage
    - **USER**: Can search assets assigned to them (unless they have custom roles)
    - **CUSTOM ROLE**: Must have ASSET_MANAGEMENT.read permission

    ## Features
    - **Full-text search** across name, description, model, manufacturer, serial number, 
      location name, location code, and location address
    - **Multi-filter support** with exact and partial matching
    - **Flexible sorting** with 9 sort fields
    - **Pagination** with configurable page size (max 100)

    ## Query Examples
    - `GET /assets/search?q=dell&asset_condition=ACTIVE`
    - `GET /assets/search?department_id=uuid&sort_by=purchase_date&sort_order=desc`
    - `GET /assets/search?q=mumbai+office&tag_state=TAGGED`
    - `GET /assets/search?location_id=uuid&last_scanned_from=2026-01-01`
    """
)
def search_assets_endpoint(
    current_user: dict = Depends(check_permission("ASSET_MANAGEMENT", "read")),
    db: Session = Depends(get_db),
    q: Optional[str] = Query(None, description="Search across name, description, model, manufacturer, serial number, and location", example="Dell Laptop", min_length=1, max_length=100),
    client_id: Optional[str] = Query(None, description="Filter by client ID. Applicable only for ADMIN users.", example="550e8400-e29b-41d4-a716-446655440000"),
    category_id: Optional[str] = Query(None, description="Filter by category ID", example="550e8400-e29b-41d4-a716-446655440001"),
    type_id: Optional[str] = Query(None, description="Filter by type ID", example="550e8400-e29b-41d4-a716-446655440002"),
    department_id: Optional[str] = Query(None, description="Filter by department ID", example="550e8400-e29b-41d4-a716-446655440003"),
    location_id: Optional[str] = Query(None, description="Filter by location ID", example="550e8400-e29b-41d4-a716-446655440004"),
    assigned_to_user_id: Optional[str] = Query(None, description="Filter by assigned user ID", example="550e8400-e29b-41d4-a716-446655440005"),
    asset_condition: Optional[AssetConditionLiteral] = Query(None, description="Filter by asset condition"),
    tag_state: Optional[TagStateLiteral] = Query(None, description="Filter by tag state"),
    manufacturer: Optional[str] = Query(None, description="Filter by manufacturer (partial match)", example="Dell", min_length=1, max_length=100),
    serial_number: Optional[str] = Query(None, description="Filter by serial number (exact match)", example="SN-12345-ABC", min_length=1, max_length=50),
    created_by: Optional[str] = Query(None, description="Filter by creator user ID. ADMIN/CLIENT_ADMIN only.", example="550e8400-e29b-41d4-a716-446655440006"),
    purchase_start_date: Optional[date] = Query(None, description="Purchase date greater than or equal", example="2024-01-01"),
    purchase_end_date: Optional[date] = Query(None, description="Purchase date less than or equal", example="2024-12-31"),
    last_scanned_from: Optional[datetime] = Query(None, description="Last scanned date from", example="2026-06-01T00:00:00Z"),
    last_scanned_to: Optional[datetime] = Query(None, description="Last scanned date to", example="2026-06-24T23:59:59Z"),
    sort_by: SortByLiteral = Query("created_at", description="Sort field", example="last_scanned_at"),
    sort_order: SortOrderLiteral = Query("desc", description="Sort order (ascending or descending)", example="desc"),
    page: int = Query(1, ge=1, description="Page number (starts from 1)", example=1),
    limit: int = Query(20, ge=1, le=100, description="Number of items per page (max 100)", example=20)
):
    # Validate client_id permission
    if client_id and current_user["role"] != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Only platform administrators can filter by client_id"
        )
    
    # Validate created_by permission
    if created_by and current_user["role"] not in ["ADMIN", "CLIENT_ADMIN"]:
        raise HTTPException(
            status_code=403,
            detail="Only ADMIN or CLIENT_ADMIN can filter by creator"
        )
    
    # Validate date ranges
    if purchase_start_date and purchase_end_date and purchase_start_date > purchase_end_date:
        raise HTTPException(
            status_code=400,
            detail="purchase_start_date cannot be greater than purchase_end_date"
        )
    
    if last_scanned_from and last_scanned_to and last_scanned_from > last_scanned_to:
        raise HTTPException(
            status_code=400,
            detail="last_scanned_from cannot be greater than last_scanned_to"
        )
    
    # Call the search service
    result = search_assets(
        db=db,
        current_user=current_user,
        q=q,
        client_id=client_id,
        category_id=category_id,
        type_id=type_id,
        department_id=department_id,
        location_id=location_id,
        assigned_to_user_id=assigned_to_user_id,
        asset_condition=asset_condition,
        tag_state=tag_state,
        manufacturer=manufacturer,
        serial_number=serial_number,
        created_by=created_by,
        purchase_start_date=purchase_start_date,
        purchase_end_date=purchase_end_date,
        last_scanned_from=last_scanned_from,
        last_scanned_to=last_scanned_to,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        limit=limit
    )
    
    return result

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
    
    # Base Query with Eager Loading
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

    # Role-Based Access Control
    user_role = current_user.get("role")
    
    # Platform Admin
    if user_role == "ADMIN":
        if client_id:
            query = query.filter(Asset.client_id == client_id)
    else:
        # Must filter by client
        query = query.filter(Asset.client_id == current_user["client_id"])
        
        # Manager - can see assets in their departments
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
        
        # Normal User (without custom role)
        elif user_role == "USER" and not current_user.get("custom_role_id"):
            query = query.filter(Asset.assigned_to_user_id == current_user["id"])

    # Full-Text Search
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

    # Exact Filters
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

    # Partial Match Filters
    if manufacturer:
        query = query.filter(Asset.manufacturer.ilike(f"%{manufacturer}%"))
    if serial_number:
        query = query.filter(Asset.serial_number == serial_number)

    # Date Range Filters
    if purchase_start_date:
        query = query.filter(Asset.purchase_date >= purchase_start_date)
    if purchase_end_date:
        query = query.filter(Asset.purchase_date <= purchase_end_date)
    if last_scanned_from:
        query = query.filter(Asset.last_scanned_at >= last_scanned_from)
    if last_scanned_to:
        query = query.filter(Asset.last_scanned_at <= last_scanned_to)

    # Sorting
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

    # Pagination
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



from app.schemas.transfers import (
    AssetTransferRequest
)
from app.services.transfers import transfer_asset  # ✅ Correct path
@router.post(
    "/{asset_id}/transfer",
    response_model=AssetResponse,
    summary="Transfer Asset"
)
def transfer_existing_asset(
    asset_id: str,
    payload: AssetTransferRequest,
    db: Session = Depends(get_db),
    current_user=Depends(
        check_permission(
            "ASSET_MANAGEMENT",
            "update"
        )
    )
):
    return transfer_asset(
        db,
        asset_id,
        payload,
        current_user
    )


from app.schemas.transfers import (
    TransferHistoryResponse
)
@router.get(
    "/{asset_id}/transfers",
    response_model=list[
        TransferHistoryResponse
    ],
    summary="Fetch Asset Transfer History",
    description="""
    Fetch complete transfer history
    of an asset.

    Access:
    - ADMIN
    - CLIENT_ADMIN
    - MANAGER
    - USER with
      ASSET_MANAGEMENT.read
    - Assigned USER
    """
)
def fetch_asset_transfers(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
        check_permission(
            "ASSET_MANAGEMENT",
            "read"
        )
    )
):
    return asset_service.get_asset_transfers(
        db,
        asset_id,
        current_user
    )


@router.post(
    "/{asset_id}/mark-lost",
    response_model=AssetResponse,
    summary="Mark Asset as Lost"
)
def mark_lost_asset(
    asset_id: str,
    payload: MarkLostRequest,
    db: Session = Depends(get_db),
    current_user=Depends(
        check_permission(
            "ASSET_MANAGEMENT",
            "update"
        )
    )
):
    return asset_service.mark_asset_lost(
        db,
        asset_id,
        payload,
        current_user
    )


@router.get(
    "/{asset_id}/timeline",
    response_model=list[
        AssetTimelineItem
    ],
    summary="Fetch Asset Timeline",
    description="""
    Returns complete lifecycle
    history of an asset.

    Includes:

    - Created
    - Verified
    - Transfers
    - Maintenance
    - Lost
    - Restored
    - Future events
    """
)
def fetch_asset_timeline(
    asset_id: str,
    db: Session = Depends(
        get_db
    ),
    current_user=Depends(
        check_permission(
            "ASSET_MANAGEMENT",
            "read"
        )
    )
):
    return asset_service.get_asset_timeline(
        db,
        asset_id,
        current_user
    )


@router.post(
    "/{asset_id}/maintenance",
    response_model=
    MaintenanceTaskResponse,
    summary=
    "Create Maintenance Task"
)
def create_asset_maintenance(
    asset_id: str,
    payload:
    CreateMaintenanceRequest,
    db: Session = Depends(
        get_db
    ),
    current_user=Depends(
        check_permission(
            "ASSET_MANAGEMENT",
            "update"
        )
    )
):
    return (
        asset_service
        .create_maintenance_task(
            db,
            asset_id,
            payload,
            current_user
        )
    )



@router.get(
    "/maintenance",
    response_model=
    list[
        MaintenanceTaskResponse
    ]
)
def fetch_maintenance_tasks(
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(
        check_permission(
            "ASSET_MANAGEMENT",
            "read"
        )
    )
):
    return (
        asset_service
        .get_maintenance_tasks(
            db,
            current_user,
            status
        )
    )



@router.post(
    "/maintenance/{task_id}/complete",
    response_model=
    MaintenanceTaskResponse
)
def complete_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
        check_permission(
            "ASSET_MANAGEMENT",
            "update"
        )
    )
):
    return (
        asset_service
        .complete_maintenance_task(
            db,
            task_id,
            current_user
        )
    )


@router.post(
    "/maintenance/{task_id}/start",
    response_model=
    MaintenanceTaskResponse
)
def start_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
        check_permission(
            "ASSET_MANAGEMENT",
            "update"
        )
    )
):
    return (
        asset_service
        .start_maintenance_task(
            db,
            task_id,
            current_user
        )
    )



@router.post(
    "/maintenance/{task_id}/approve",
    response_model=
    MaintenanceTaskResponse
)
def approve_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
        check_permission(
            "ASSET_MANAGEMENT",
            "update"
        )
    )
):
    return (
        asset_service
        .approve_maintenance_task(
            db,
            task_id,
            current_user
        )
    )



@router.get(
    "/maintenance/{task_id}",
    response_model=
    MaintenanceTaskResponse
)
def fetch_maintenance_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
        check_permission(
            "ASSET_MANAGEMENT",
            "read"
        )
    )
):
    return (
        asset_service
        .get_maintenance_task(
            db,
            task_id,
            current_user
        )
    )



@router.get(
    "/maintenance",
    response_model=
    list[
        MaintenanceTaskResponse
    ]
)
def fetch_maintenance_tasks(
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(
        check_permission(
            "ASSET_MANAGEMENT",
            "read"
        )
    )
):
    return (
        asset_service
        .get_maintenance_tasks(
            db,
            current_user,
            status
        )
    )



@router.post(
    "/{asset_id}/maintenance",
    response_model=
    MaintenanceTaskResponse
)
def create_asset_maintenance(
    asset_id: str,
    payload:
    CreateMaintenanceRequest,
    db: Session = Depends(get_db),
    current_user=Depends(
        check_permission(
            "ASSET_MANAGEMENT",
            "update"
        )
    )
):
    return (
        asset_service
        .create_maintenance_task(
            db,
            asset_id,
            payload,
            current_user
        )
    )