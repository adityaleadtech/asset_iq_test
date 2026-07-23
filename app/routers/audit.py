# app/routers/audit.py

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.config.dependencies import get_current_user, get_db
from app.models.users import User
from app.schemas.Audit import (
    AuditDetailsResponse,
    AuditPlanCreate,
    AuditPlanListResponse,
    AuditPlanResponse,
    AuditPlanUpdate,
    AuditSessionResponse,
    AuditSessionListResponse,
    AuditResultRequest,
    AuditResultResponse,
    AuditDashboardResponse,
    MyAuditResponse,
    ScanAssetRequest,
    ScanAssetResponse,
    SubmitAssetAuditRequest,
    SubmitAssetAuditResponse,
    AuditSummaryResponse,
)
from app.enums.audit_enums import AuditPlanStatus, AuditSessionStatus
from app.services.audit import AuditService

router = APIRouter(prefix="/audits", tags=["Audits"])

# ============================================================
# ADMIN ENDPOINTS
# ============================================================

@router.post(
    "",
    response_model=AuditPlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Audit Plan",
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
    summary="Get Audit Plan Details (Admin)",
)
def get_audit_plan_by_id(
    audit_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin endpoint for getting audit plan details with all sessions."""
    return AuditService.get_audit_by_id(
        audit_id=audit_id,
        db=db,
        current_user=current_user
    )


@router.patch(
    "/{audit_id}",
    response_model=AuditPlanResponse,
    summary="Update Audit Plan",
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
# MOBILE AUDITOR ENDPOINTS
# ============================================================

@router.get(
    "/my-audits",
    response_model=list[MyAuditResponse],
    summary="Get My Audits",
)
def get_my_audits(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return AuditService.get_my_audits_simple(
        db,
        current_user
    )


@router.get(
    "/{audit_id}",
    response_model=AuditDetailsResponse,
    summary="Get Audit Details (Mobile)",
)
def get_audit_details(
    audit_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Mobile endpoint for getting audit details with asset list."""
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
)
def start_audit_session(
    audit_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start an audit session by audit plan ID."""
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
)
def scan_asset(
    audit_id: str,
    request: ScanAssetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Scan an asset during an audit.
    
    The frontend sends the AssetIQ asset ID obtained from either
    a QR code or an RFID scan.
    """
    return AuditService.scan_asset(
        db=db,
        audit_id=audit_id,
        asset_id=request.asset_id,
        current_user=current_user
    )


@router.post(
    "/{audit_id}/assets/{asset_id}",
    response_model=SubmitAssetAuditResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit Asset Audit",
)
def submit_asset_audit(
    audit_id: str,
    asset_id: str,
    request: SubmitAssetAuditRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit audit findings for a scanned asset.
    """
    return AuditService.submit_asset_audit(
        db=db,
        audit_id=audit_id,
        asset_id=asset_id,
        request=request,
        current_user=current_user
    )


@router.get(
    "/{audit_id}/summary",
    response_model=AuditSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Audit Summary",
)
def get_audit_summary(
    audit_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get summary statistics for an audit.
    
    Returns:
    - Total assets
    - Audited vs pending counts
    - Completion percentage
    - Breakdown by status (in_place, dislocated, missing, etc.)
    """
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
)
def complete_audit(
    audit_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually complete an audit session.
    
    Only allowed when all assets have been audited.
    """
    return AuditService.complete_audit_session_manual(
        db=db,
        audit_id=audit_id,
        current_user=current_user
    )


# ============================================================
# DEPRECATED / LEGACY ENDPOINTS (to be removed)
# ============================================================

@router.get(
    "/sessions/{session_id}/assets",
    response_model=list[AuditResultResponse],
    summary="[DEPRECATED] Get Assets for Audit Session",
    deprecated=True
)
def get_session_assets_deprecated(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deprecated: Use /{audit_id} instead."""
    return AuditService.get_session_assets(
        session_id=session_id,
        db=db,
        current_user=current_user
    )


@router.post(
    "/sessions/{session_id}/assets/{asset_id}",
    response_model=AuditResultResponse,
    status_code=status.HTTP_200_OK,
    summary="[DEPRECATED] Submit Asset Audit",
    deprecated=True
)
def submit_asset_audit_deprecated(
    session_id: str,
    asset_id: str,
    payload: AuditResultRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deprecated: Use /{audit_id}/assets/{asset_id} instead."""
    return AuditService.submit_asset_audit_legacy(
        session_id=session_id,
        asset_id=asset_id,
        payload=payload,
        db=db,
        current_user=current_user
    )


@router.post(
    "/sessions/{session_id}/complete",
    response_model=AuditSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="[DEPRECATED] Complete Audit Session",
    deprecated=True
)
def complete_audit_session_deprecated(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deprecated: Use /{audit_id}/complete instead."""
    return AuditService.complete_audit_session(
        session_id=session_id,
        db=db,
        current_user=current_user
    )


