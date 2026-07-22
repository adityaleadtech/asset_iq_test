from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.config.dependencies import get_current_user, get_db
from app.models.users import User
from app.schemas.Audit import (
    AuditPlanCreate,
    AuditPlanListResponse,
    AuditPlanResponse,
    AuditPlanUpdate,
    AuditSessionResponse,
    AuditSessionListResponse,
    AuditResultRequest,
    AuditResultResponse,
    AuditDashboardResponse,
)
from app.enums.audit_enums import AuditPlanStatus, AuditSessionStatus
from app.services.audit import AuditService

router = APIRouter(prefix="/audits", tags=["Audits"])


@router.post(
    "",
    response_model=AuditPlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Audit Plan",
    description="""
    Creates a new audit plan.

    Frontend Usage:
    - Used by Platform Admin and Client Admin.
    - Select audit name, frequency, auditor, and audit targets.
    - Targets can be Locations, Departments, Categories, or Individual Assets.
    - Automatically creates the first audit session.
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
    Returns a paginated list of audit plans.

    Frontend Usage:
    - Populate the Audit Management table.
    - Supports pagination, search, and status filtering.
    - Platform Admin sees all audits.
    - Client Admin sees audits of their client.
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
    "/my",
    response_model=AuditSessionListResponse,
    summary="Get My Assigned Audits",
    description="""
    Returns audit sessions assigned to the logged-in user.

    Frontend Usage:
    - Home screen of the mobile application.
    - Displays assigned audits.
    - Employee selects one audit to begin.
    - Supports filtering by audit session status.
    """
)
def get_my_audits(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[AuditSessionStatus] = Query(None, description="Filter by session status")
):
    return AuditService.get_my_audits(
        db=db,
        current_user=current_user,
        page=page,
        size=size,
        status=status
    )


@router.get(
    "/dashboard",
    response_model=AuditDashboardResponse,
    summary="Audit Dashboard",
    description="""
    Returns audit statistics.

    Frontend Usage:
    - Dashboard cards.
    - Total audits.
    - Active audits.
    - Pending sessions.
    - Completed sessions.
    - Total assets.
    - Audited assets.
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
    Returns completed audit sessions.

    Frontend Usage:
    - Audit History screen.
    - Shows completed audits with assigned auditor,
    completion time and audited asset count.
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


@router.get(
    "/{audit_id}",
    response_model=AuditPlanResponse,
    summary="Get Audit Details",
    description="""
    Returns complete details of an audit plan.

    Frontend Usage:
    - Open Audit Details page.
    - Displays assigned auditor.
    - Displays targets.
    - Displays audit schedule.
    - Displays all audit sessions.
    """
)
def get_audit_by_id(
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
    Updates an existing audit plan.

    Frontend Usage:
    - Edit Audit screen.
    - Allows changing frequency, auditor,
    status and audit details before execution.
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
    Soft deletes an audit plan.

    Frontend Usage:
    - Delete action from Audit Management page.
    - Cannot delete audits that currently have an
    active audit session.
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


@router.post(
    "/sessions/{session_id}/start",
    response_model=AuditSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Start Audit Session",
    description="""
    Starts an assigned audit session.

    Frontend Usage:
    - Employee presses the Start Audit button.
    - Generates audit records for every asset included
    in the audit.
    - Changes session status to IN_PROGRESS.
    """
)
def start_audit_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return AuditService.start_audit_session(
        session_id=session_id,
        db=db,
        current_user=current_user
    )


@router.get(
    "/sessions/{session_id}/assets",
    response_model=list[AuditResultResponse],
    summary="Get Assets for Audit Session",
    description="""
    Returns all assets included in an audit session.

    Frontend Usage:
    - Asset List screen.
    - Displays every asset that needs verification.
    - Shows audit status for each asset.
    - Employee selects an asset to perform verification.
    """
)
def get_session_assets(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Note: You'll need to implement this method in AuditService
    return AuditService.get_session_assets(
        session_id=session_id,
        db=db,
        current_user=current_user
    )


@router.post(
    "/sessions/{session_id}/assets/{asset_id}",
    response_model=AuditResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit Asset Audit",
    description="""
    Submits verification for a single asset.

    Frontend Usage:
    - Asset Verification screen.
    - Upload captured image.
    - Submit GPS coordinates.
    - Submit remarks.
    - Submit asset condition.
    - Submit actual location.
    - Marks the asset as audited.
    """
)
def submit_asset_audit(
    session_id: str,
    asset_id: str,
    payload: AuditResultRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return AuditService.submit_asset_audit(
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
    summary="Complete Audit Session",
    description="""
    Completes an audit session.

    Frontend Usage:
    - Employee presses Complete Audit.
    - Allowed only after every asset has been verified.
    - Marks the session as COMPLETED.
    - Automatically schedules the next audit session
    based on the audit frequency.
    """
)
def complete_audit_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return AuditService.complete_audit_session(
        session_id=session_id,
        db=db,
        current_user=current_user
    )