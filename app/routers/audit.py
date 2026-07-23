from fastapi import APIRouter, Depends, Query, status, Form, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.config.dependencies import get_current_user, get_db
from app.models.users import User
from app.schemas.Audit import (
    AuditDetailsResponse,
    AuditPlanCreate,
    AuditAssetDetailsResponse,
    AuditPlanListResponse,
    AuditPlanResponse,
    AuditPlanUpdate,
    AuditReportResponse,
    AuditSessionResponse,
    AuditDashboardResponse,
    MyAuditResponse,
    ScanAssetRequest,
    ScanAssetResponse,
    SubmitAssetAuditResponse,
    AuditSummaryResponse,
)
from app.enums.audit_enums import AuditPlanStatus, AuditSessionStatus, AuditResultStatus, AssetConditionStatus
from app.services.audit import AuditService
from app.utils.auth import admin_required

router = APIRouter(prefix="/audits", tags=["Audits"])

# ============================================================
# 🌐 WEB ADMIN ENDPOINTS - STATIC ROUTES FIRST
# ============================================================

@router.post(
    "",
    response_model=AuditPlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Audit Plan",
    description="""
    🌐 Web Admin Only

    Creates a new audit plan for a client by assigning an auditor and selecting
    which assets should be audited.

    The audit can target:
    • Individual Assets
    • Locations
    • Departments
    • Asset Categories

    Workflow:
    1. Validate the client.
    2. Validate the assigned auditor.
    3. Validate all audit targets.
    4. Create the audit plan.
    5. Create the initial pending audit session.

    This endpoint is the starting point of the entire audit workflow.
    """
)
def create_audit(
    payload: AuditPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return AuditService.create_audit(
        payload=payload,
        db=db,
        current_user=current_user
    )


@router.get(
    "",
    response_model=AuditPlanListResponse,
    summary="Get Audit Plans",
    description="""
    🌐 Web Admin Only

    Returns a paginated list of audit plans.

    Supports:
    • Pagination
    • Search by audit name
    • Status filtering (planned, in_progress, completed)

    Platform Admins can view audits across all clients.

    Client Admins can only view audits belonging to their client.
    """
)
def get_audits_router(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by audit name"),
    status: Optional[AuditPlanStatus] = Query(None, description="Filter by status")
):
    return AuditService.get_audits(
        db=db,
        current_user=current_user,
        page=page,
        size=size,
        search=search,
        status=status
    )


@router.get(
    "/dashboard",
    response_model=AuditDashboardResponse,
    summary="Audit Dashboard",
    description="""
    🌐 Web Admin Only

    Returns high-level audit statistics.

    Includes:
    • Total audits
    • Active audits
    • Pending audit sessions
    • Completed audit sessions
    • Audits currently in progress
    • Total assets scheduled for audit
    • Total assets already audited

    Used to populate the Audit Dashboard.
    """
)
def audit_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return AuditService.audit_dashboard(
        db=db,
        current_user=current_user
    )


# ============================================================
# 📱 MOBILE AUDITOR ENDPOINTS - STATIC ROUTES FIRST
# ============================================================

@router.get(
    "/my-audits",
    response_model=list[MyAuditResponse],
    summary="Get My Audits",
    description="""
    📱 Mobile App Only

    Returns all audit sessions assigned to the logged-in auditor.

    Each audit includes:
    • Audit name
    • Scheduled date
    • Status
    • Total assets
    • Audited assets
    • Completion percentage

    This is the first API called after the auditor logs into the mobile application.
    """
)
def get_my_audits(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    print(f"MY AUDITS CALLED - User: {current_user.id if hasattr(current_user, 'id') else current_user.get('id')}")
    return AuditService.get_my_audits_simple(
        db=db,
        current_user=current_user
    )


# ============================================================
# 🌐 WEB ADMIN ENDPOINTS - PARAMETERIZED ROUTES
# ============================================================

@router.get(
    "/{audit_id}",
    response_model=AuditPlanResponse,
    summary="Get Audit Plan Details (Admin)",
    description="""
    🌐 Web Admin Only

    Returns complete information about an audit plan.

    Includes:
    • Audit information
    • Assigned auditor
    • Audit frequency
    • Schedule
    • Next execution date
    • Every audit session created for this audit

    Useful for monitoring audit progress and reviewing previous audit executions.
    """
)
def get_audit_by_id_admin(
    audit_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return AuditService.get_audit_by_id(
        audit_id=audit_id,
        db=db,
        current_user=current_user
    )


@router.patch(
    "/{audit_id}",
    response_model=AuditPlanResponse,
    summary="Update Audit Plan",
    description="""
    🌐 Web Admin Only

    Updates an existing audit plan.

    Supported updates:
    • Audit name
    • Description
    • Assigned auditor
    • Frequency
    • Schedule
    • Audit status

    If the assigned auditor changes, all pending audit sessions are automatically
    reassigned to the new auditor.
    """
)
def update_audit(
    audit_id: str,
    payload: AuditPlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return AuditService.update_audit(
        audit_id=audit_id,
        payload=payload,
        db=db,
        current_user=current_user
    )


@router.delete(
    "/{audit_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Audit Plan",
    description="""
    🌐 Web Admin Only

    Soft deletes an audit plan.

    Rules:
    • Active audit sessions cannot be deleted.
    • Only audits without an IN_PROGRESS session can be removed.
    • Data is preserved for historical reporting.

    The audit is marked inactive instead of being permanently removed.
    """
)
def delete_audit(
    audit_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return AuditService.delete_audit(
        audit_id=audit_id,
        db=db,
        current_user=current_user
    )


# ============================================================
# 📱 MOBILE AUDITOR ENDPOINTS - PARAMETERIZED ROUTES
# ============================================================

@router.get(
    "/{audit_id}/mobile",
    response_model=AuditDetailsResponse,
    summary="Get Audit Details (Mobile)",
    description="""
    📱 Mobile App Only

    Returns detailed information about a selected audit for the mobile app.

    Includes:
    • Audit information
    • Audit schedule
    • Asset list
    • Current progress
    • Completion percentage
    • Audit status of every asset

    The mobile application calls this endpoint before starting the audit.
    """
)
def get_audit_details_mobile(
    audit_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return AuditService.get_audit_details(
        db=db,
        audit_id=audit_id,
        current_user=current_user
    )


@router.post(
    "/{audit_id}/start",
    response_model=AuditSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Start Audit Session",
    description="""
    📱 Mobile App Only

    Starts the selected audit.

    Workflow:
    1. Verify auditor assignment.
    2. Verify a pending audit session exists.
    3. Mark the session as IN_PROGRESS.
    4. Discover every asset included in the audit.
    5. Create a pending AuditResult record for each asset.

    No audit findings are recorded at this stage.
    """
)
def start_audit_session(
    audit_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return AuditService.start_audit_session_by_plan(
        audit_id=audit_id,
        db=db,
        current_user=current_user
    )


@router.post(
    "/{audit_id}/scan",
    response_model=ScanAssetResponse,
    status_code=status.HTTP_200_OK,
    summary="Scan Asset",
    description="""
    📱 Mobile App Only

    Validates a QR code or RFID scan.

    The mobile application sends the internal AssetIQ asset ID obtained
    from the scanned QR code or RFID tag.

    Validation performed:
    • Audit session is active
    • Asset exists
    • Asset belongs to the audit
    • Asset has not already been audited

    Returns asset information for verification before submitting the audit result.
    """
)
def scan_asset(
    audit_id: str,
    request: ScanAssetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return AuditService.scan_asset(
        db=db,
        audit_id=audit_id,
        asset_id=request.asset_id,
        current_user=current_user
    )


@router.get(
    "/{audit_id}/assets/{asset_id}",
    response_model=AuditAssetDetailsResponse,
    summary="Get Asset Details",
    description="""
    📱 Mobile App Only

    Returns complete information about a scanned asset.

    This endpoint is called immediately after a successful scan to
    populate the editable audit form.

    The returned information is read-only. The auditor only edits
    the audit findings such as condition, quantity, remarks,
    photo, and GPS location.
    """
)
def get_asset_details(
    audit_id: str,
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return AuditService.get_asset_details(
        db=db,
        audit_id=audit_id,
        asset_id=asset_id,
        current_user=current_user
    )


@router.patch(
    "/{audit_id}/assets/{asset_id}",
    response_model=SubmitAssetAuditResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit Asset Audit",
    description="""
    📱 Mobile App Only

    Updates the audit result for a scanned asset.

    The auditor submits:
    • Audit status
    • Asset condition
    • Quantity found
    • Remarks
    • GPS location
    • Asset image

    The uploaded image is stored and linked to the audit result.

    **Audit Status Options:**
    - `IN_PLACE`: Asset is physically present and in its designated location
    - `DISLOCATED`: Asset is found but not in its designated location
    - `NOT_FOUND`: Asset cannot be located
    - `LOST`: Asset is confirmed lost

    **Condition Status Options:**
    - `EXCELLENT`: Asset is in perfect condition with no defects
    - `GOOD`: Asset has minor wear and tear but is fully functional
    - `FAIR`: Asset has noticeable defects but is operational
    - `POOR`: Asset has significant defects affecting functionality
    - `DAMAGED`: Asset is damaged and requires repair or replacement
    - `VERY_POOR`: Asset is severely damaged and not operational

    **Location Status (Auto-calculated based on GPS):**
    - `VERIFIED`: Asset is within geofence radius
    - `NEARBY`: Asset is within 2x geofence radius
    - `OUTSIDE_GEOFENCE`: Asset is outside geofence
    - `LOCATION_UNKNOWN`: Location cannot be determined

    **Quantity Found:**
    - Must be greater than 0
    - Should match expected quantity based on inventory records
    """
)
def submit_asset_audit(
    audit_id: str,
    asset_id: str,
    status: str = Form(
        ...,
        description="Audit status: IN_PLACE, DISLOCATED, NOT_FOUND, LOST",
        example="IN_PLACE"
    ),
    condition_status: str = Form(
        ...,
        description="Asset condition: EXCELLENT, GOOD, FAIR, POOR, DAMAGED, VERY_POOR",
        example="GOOD"
    ),
    quantity_found: int = Form(
        ...,
        description="Quantity of assets found (must be > 0)",
        ge=1,
        example=5
    ),
    remarks: str | None = Form(
        None,
        description="Optional remarks or notes about the audit",
        example="Asset is in good condition but needs maintenance"
    ),
    audit_latitude: float = Form(
        ...,
        description="GPS latitude of the audit location (must be between -90 and 90)",
        ge=-90,
        le=90,
        example=12.9716
    ),
    audit_longitude: float = Form(
        ...,
        description="GPS longitude of the audit location (must be between -180 and 180)",
        ge=-180,
        le=180,
        example=77.5946
    ),
    photo: UploadFile | None = File(
        None,
        description="Photo evidence of the asset (JPEG, PNG, or WebP format)"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Validate latitude
    if not (-90 <= audit_latitude <= 90):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid latitude: {audit_latitude}. Must be between -90 and 90"
        )
    
    # Validate longitude
    if not (-180 <= audit_longitude <= 180):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid longitude: {audit_longitude}. Must be between -180 and 180"
        )
    
    # Validate audit status
    valid_statuses = ["IN_PLACE", "DISLOCATED", "NOT_FOUND", "LOST"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status: {status}. Must be one of {valid_statuses}"
        )
    
    # Validate condition status
    valid_conditions = ["EXCELLENT", "GOOD", "FAIR", "POOR", "DAMAGED", "VERY_POOR"]
    if condition_status not in valid_conditions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid condition status: {condition_status}. Must be one of {valid_conditions}"
        )
    
    return AuditService.submit_asset_audit(
        db=db,
        audit_id=audit_id,
        asset_id=asset_id,
        status=status,
        condition_status=condition_status,
        quantity_found=quantity_found,
        remarks=remarks,
        audit_latitude=audit_latitude,
        audit_longitude=audit_longitude,
        photo=photo,
        current_user=current_user
    )


@router.get(
    "/{audit_id}/summary",
    response_model=AuditSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Audit Summary",
    description="""
    📱 Mobile App Only

    Returns the current progress of the audit session.

    Includes:
    • Total assets
    • Audited assets
    • Remaining assets
    • Completion percentage
    • Assets in place
    • Dislocated assets
    • Lost assets
    • Assets not found

    Called before the auditor completes the audit.
    """
)
def get_audit_summary(
    audit_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return AuditService.get_audit_summary(
        db=db,
        audit_id=audit_id,
        current_user=current_user
    )


@router.post(
    "/{audit_id}/complete",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Complete Audit Session",
    description="""
    📱 Mobile App Only

    Completes the audit session after all assets have been audited.

    Validation:
    • Every asset must be audited.
    • Session must be IN_PROGRESS.

    On success:
    1. Marks the session as COMPLETED.
    2. Stores the completion timestamp.
    3. Updates the audit's next scheduled execution date.
    4. Automatically creates the next pending audit session for recurring audits.

    This is the final step in the mobile audit workflow.
    """
)
def complete_audit(
    audit_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return AuditService.complete_audit_session_manual(
        db=db,
        audit_id=audit_id,
        current_user=current_user
    )

from fastapi import Depends, HTTPException, status

from app.config.dependencies import get_current_user



def admin_or_client_admin(
    current_user=Depends(get_current_user),
):
    if current_user["role"] not in [
        "ADMIN",
        "CLIENT_ADMIN"
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to perform this action."
        )

    return current_user
@router.get(
    "/{audit_id}/report",
    response_model=AuditReportResponse,
    summary="Get Audit Report"
)
def get_audit_report(
    audit_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(admin_or_client_admin)
):
    return AuditService.get_audit_report(
        db=db,
        audit_id=audit_id,
        current_user=current_user
    )