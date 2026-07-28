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
    AuditReviewResponse,  # ✅ Added missing import
)
from app.enums.audit_enums import AuditPlanStatus
from app.services.audit import AuditService

router = APIRouter(prefix="/audits", tags=["Audits"])

# ============================================================
# 🌐 WEB ADMIN ENDPOINTS - STATIC ROUTES FIRST
# ============================================================

@router.post(
    "",
    response_model=AuditPlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Audit Plan"
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
    summary="Get Audit Plans"
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
    summary="Audit Dashboard"
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
    summary="Get My Audits"
)
def get_my_audits(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
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
    summary="Get Audit Plan Details (Admin)"
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
    summary="Update Audit Plan"
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
    summary="Delete Audit Plan"
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
    summary="Get Audit Details (Mobile)"
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
    summary="Start Audit Session"
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
    summary="Scan Asset"
)
def scan_asset(
    audit_id: str,
    request: ScanAssetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return AuditService.scan_asset_wrapper(
        db=db,
        audit_id=audit_id,
        asset_id=request.asset_id,
        current_user=current_user
    )


@router.get(
    "/{audit_id}/assets/{asset_id}",
    response_model=AuditAssetDetailsResponse,
    summary="Get Asset Details"
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
    summary="Submit Asset Audit"
)
def submit_asset_audit(
    audit_id: str,
    asset_id: str,
    status: str = Form(
        ...,
        description="Audit status: IN_PLACE, DISLOCATED, NOT_FOUND, LOST"
    ),
    condition_status: str = Form(
        ...,
        description="Asset condition: EXCELLENT, GOOD, FAIR, POOR, DAMAGED, VERY_POOR"
    ),
    quantity_found: int = Form(
        ...,
        description="Quantity of assets found (must be > 0)",
        ge=1
    ),
    remarks: str | None = Form(
        None,
        description="Optional remarks or notes about the audit"
    ),
    audit_latitude: float = Form(
        ...,
        description="GPS latitude of the audit location (must be between -90 and 90)",
        ge=-90,
        le=90
    ),
    audit_longitude: float = Form(
        ...,
        description="GPS longitude of the audit location (must be between -180 and 180)",
        ge=-180,
        le=180
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
        audit_status=status,
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
    summary="Get Audit Summary"
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


@router.get(
    "/{audit_id}/review",
    response_model=AuditReviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Audit Review",
    description="""
    📱 Mobile App Only

    Returns all assets in the current audit session with their latest audit status.

    This endpoint is used before completing an audit.

    It allows the auditor to review all verified assets and identify any remaining
    pending assets. Pending assets can then be marked as LOST or NOT_FOUND using
    the existing PATCH /audits/{audit_id}/assets/{asset_id} endpoint.

    No audit data is modified by this endpoint.
    """
)
def get_audit_review(
    audit_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return AuditService.get_audit_review(
        db=db,
        audit_id=audit_id,
        current_user=current_user
    )


@router.post(
    "/{audit_id}/complete",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Complete Audit Session"
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


# ============================================================
# 🔐 ADMIN ONLY ENDPOINTS
# ============================================================

def admin_or_client_admin(
    current_user: User = Depends(get_current_user),
):
    # Handle both User object and dict
    if hasattr(current_user, 'role'):
        role = current_user.role
    elif isinstance(current_user, dict):
        role = current_user.get("role")
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to perform this action."
        )
    
    if role not in ["ADMIN", "CLIENT_ADMIN"]:
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
    current_user: User = Depends(admin_or_client_admin)
):
    return AuditService.get_audit_report(
        db=db,
        audit_id=audit_id,
        current_user=current_user
    )