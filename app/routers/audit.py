# app/routers/audit.py

from fastapi import APIRouter, Depends, Query, status, Form, File, UploadFile
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
    AuditSessionResponse,
    AuditSessionListResponse,
    AuditDashboardResponse,
    MyAuditResponse,
    ScanAssetRequest,
    ScanAssetResponse,
    SubmitAssetAuditResponse,
    AuditSummaryResponse,
)
from app.enums.audit_enums import AuditPlanStatus
from app.services.audit import AuditService

router = APIRouter(prefix="/audits", tags=["Audits"])

# ============================================================
# 🌐 WEB ADMIN ENDPOINTS
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
    • Status filtering

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
    "/plan/{audit_id}",
    response_model=AuditPlanResponse,
    summary="Get Audit Plan Details",
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
def get_audit_plan_by_id(
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


@router.get(
    "/history",
    response_model=AuditSessionListResponse,
    summary="Audit History",
    description="""
    🌐 Web Admin Only

    Returns completed audit sessions.

    Supports pagination.

    Each record contains:
    • Audit name
    • Assigned auditor
    • Completion date
    • Total assets
    • Audited assets
    • Session status

    Useful for reviewing previously completed audits.
    """
)
def audit_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page")
):
    return AuditService.audit_history(
        db=db,
        current_user=current_user,
        page=page,
        size=size
    )


# ============================================================
# 📱 MOBILE AUDITOR ENDPOINTS
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
    return AuditService.get_my_audits_simple(
        db=db,
        current_user=current_user
    )


@router.get(
    "/{audit_id}",
    response_model=AuditDetailsResponse,
    summary="Get Audit Details",
    description="""
    📱 Mobile App Only

    Returns detailed information about a selected audit.

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
def get_audit_details(
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
    """
)
def submit_asset_audit(
    audit_id: str,
    asset_id: str,
    status: str = Form(...),
    condition_status: str = Form(...),
    quantity_found: int = Form(...),
    remarks: str | None = Form(None),
    audit_latitude: float = Form(...),
    audit_longitude: float = Form(...),
    photo: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
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