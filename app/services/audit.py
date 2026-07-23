from datetime import datetime, timedelta
from fastapi import HTTPException, status, UploadFile
from sqlalchemy.orm import Session
from typing import Dict
import cloudinary.uploader
import uuid

from app.models.clients import Client
from app.models.users import User
from app.models.location import Location
from app.models.departments import Department
from app.models.asset import Asset
from app.models.asset_categories import AssetCategory
from app.models.auditplan import AuditPlan
from app.models.audittaget import AuditTarget
from app.models.auditsession import AuditSession
from app.models.AuditResult import AuditResult

from app.schemas.Audit import (
    AuditAssetDetailsResponse,
    AuditAssetResponse,
    AuditDetailsResponse,
    AuditPlanCreate,
    AuditPlanListResponse,
    AuditPlanResponse,
    AuditPlanUpdate,
    AuditSessionResponse,
    AuditSessionListResponse,
    AuditDashboardResponse,
    AuditSummaryResponse,
    MyAuditResponse,
    ScanAssetResponse,
    SubmitAssetAuditResponse,
)

from app.enums.audit_enums import (
    AuditFrequencyUnit,
    AuditPlanStatus,
    AuditSessionStatus,
    AuditTargetType,
    AuditResultStatus,
)


class AuditService:

    @staticmethod
    def create_audit(
        payload: AuditPlanCreate,
        db: Session,
        current_user: User
    ):

        try:

            # ---------------------------------
            # Resolve Client
            # ---------------------------------

            if current_user["role"] == "PLATFORM_ADMIN":

                if not payload.client_id:
                    raise HTTPException(
                        status_code=400,
                        detail="client_id is required."
                    )

                client_id = payload.client_id

            elif current_user["role"] == "CLIENT_ADMIN":

                client_id = current_user["client_id"]

            else:
                raise HTTPException(
                    status_code=403,
                    detail="Permission denied."
                )

            # ---------------------------------
            # Validate Client
            # ---------------------------------

            client = (
                db.query(Client)
                .filter(
                    Client.id == client_id,
                    Client.is_active == True
                )
                .first()
            )

            if not client:
                raise HTTPException(
                    status_code=404,
                    detail="Client not found."
                )

            # ---------------------------------
            # Validate Auditor
            # ---------------------------------

            auditor = (
                db.query(User)
                .filter(
                    User.id == payload.auditor_id,
                    User.client_id == client_id,
                    User.is_active == True
                )
                .first()
            )

            if not auditor:
                raise HTTPException(
                    status_code=404,
                    detail="Auditor not found."
                )

            # ---------------------------------
            # Duplicate Targets
            # ---------------------------------

            seen = set()

            for target in payload.targets:

                key = (
                    target.target_type,
                    target.target_id,
                )

                if key in seen:
                    raise HTTPException(
                        status_code=400,
                        detail="Duplicate audit target."
                    )

                seen.add(key)

            # ---------------------------------
            # Validate Targets
            # ---------------------------------

            for target in payload.targets:

                if target.target_type == AuditTargetType.LOCATION:

                    exists = (
                        db.query(Location)
                        .filter(
                            Location.id == target.target_id,
                            Location.client_id == client_id,
                            Location.is_active == True,
                        )
                        .first()
                    )

                    if not exists:
                        raise HTTPException(
                            status_code=404,
                            detail=f"Location {target.target_id} not found."
                        )

                elif target.target_type == AuditTargetType.DEPARTMENT:

                    exists = (
                        db.query(Department)
                        .filter(
                            Department.id == target.target_id,
                            Department.client_id == client_id,
                            Department.is_active == True,
                        )
                        .first()
                    )

                    if not exists:
                        raise HTTPException(
                            status_code=404,
                            detail=f"Department {target.target_id} not found."
                        )

                elif target.target_type == AuditTargetType.CATEGORY:

                    exists = (
                        db.query(AssetCategory)
                        .filter(
                            AssetCategory.id == target.target_id,
                            AssetCategory.is_active == True,
                        )
                        .first()
                    )

                    if not exists:
                        raise HTTPException(
                            status_code=404,
                            detail=f"Category {target.target_id} not found."
                        )

                    if (
                        exists.client_id
                        and exists.client_id != client_id
                    ):
                        raise HTTPException(
                            status_code=400,
                            detail="Category belongs to another client."
                        )

                elif target.target_type == AuditTargetType.ASSET:

                    exists = (
                        db.query(Asset)
                        .filter(
                            Asset.id == target.target_id,
                            Asset.client_id == client_id,
                            Asset.is_active == True,
                        )
                        .first()
                    )

                    if not exists:
                        raise HTTPException(
                            status_code=404,
                            detail=f"Asset {target.target_id} not found."
                        )

                else:
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid target type."
                    )

            # ---------------------------------
            # Next Run Date
            # ---------------------------------

            if payload.frequency_unit == AuditFrequencyUnit.DAY:

                next_run_date = (
                    payload.start_date +
                    timedelta(days=payload.frequency_interval)
                )

            elif payload.frequency_unit == AuditFrequencyUnit.WEEK:

                next_run_date = (
                    payload.start_date +
                    timedelta(weeks=payload.frequency_interval)
                )

            else:

                next_run_date = (
                    payload.start_date +
                    timedelta(days=30 * payload.frequency_interval)
                )

            # ---------------------------------
            # Create Audit Plan
            # ---------------------------------

            audit_plan = AuditPlan(

                client_id=client_id,

                name=payload.name,

                description=payload.description,

                auditor_id=payload.auditor_id,

                frequency_unit=payload.frequency_unit,

                frequency_interval=payload.frequency_interval,

                start_date=payload.start_date,

                end_date=payload.end_date,

                next_run_date=next_run_date,

                status=AuditPlanStatus.ACTIVE,

                created_by=current_user["id"],

                is_active=True,
            )

            db.add(audit_plan)

            db.flush()

            # ---------------------------------
            # Create Audit Targets
            # ---------------------------------

            for target in payload.targets:

                audit_target = AuditTarget(

                    audit_plan_id=audit_plan.id,

                    target_type=target.target_type,

                    target_id=target.target_id

                )

                db.add(audit_target)

            # ---------------------------------
            # Create Initial Audit Session
            # ---------------------------------

            audit_session = AuditSession(

                audit_plan_id=audit_plan.id,

                assigned_to=payload.auditor_id,

                scheduled_date=payload.start_date,

                status=AuditSessionStatus.PENDING,

                total_assets=0,

                audited_assets=0,

                started_at=None,

                completed_at=None,

                conducted_by=None

            )

            db.add(audit_session)

            db.commit()

            db.refresh(audit_plan)
            db.refresh(audit_session)

            return AuditPlanResponse(

                id=audit_plan.id,

                name=audit_plan.name,

                description=audit_plan.description,

                auditor_id=auditor.id,

                auditor_name=auditor.full_name,

                frequency_unit=audit_plan.frequency_unit,

                frequency_interval=audit_plan.frequency_interval,

                start_date=audit_plan.start_date,

                end_date=audit_plan.end_date,

                next_run_date=audit_plan.next_run_date,

                status=audit_plan.status,

                created_at=audit_plan.created_at

            )

        except HTTPException:
            db.rollback()
            raise

        except Exception as e:

            db.rollback()

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    @staticmethod
    def get_audits(
        db: Session,
        current_user: User,
        page: int = 1,
        size: int = 10,
        search: str | None = None,
        status: AuditPlanStatus | None = None,
    ):
        query = (
            db.query(AuditPlan)
            .join(User, AuditPlan.auditor_id == User.id)
            .filter(AuditPlan.is_active == True)
        )

        # ---------------------------------
        # Role Filter
        # ---------------------------------

        if current_user["role"] == "PLATFORM_ADMIN":

            pass

        elif current_user["role"] == "CLIENT_ADMIN":

            query = query.filter(
                AuditPlan.client_id == current_user["client_id"]
            )

        elif current_user["role"] == "AUDITOR":

            query = query.filter(
                AuditPlan.auditor_id == current_user["id"]
            )

        else:

            raise HTTPException(
                status_code=403,
                detail="Permission denied."
            )

        # ---------------------------------
        # Search
        # ---------------------------------

        if search:

            query = query.filter(
                AuditPlan.name.ilike(f"%{search}%")
            )

        # ---------------------------------
        # Status Filter
        # ---------------------------------

        if status:

            query = query.filter(
                AuditPlan.status == status
            )

        # ---------------------------------
        # Count
        # ---------------------------------

        total = query.count()

        # ---------------------------------
        # Pagination
        # ---------------------------------

        audits = (
            query.order_by(AuditPlan.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )

        items = []

        for audit in audits:

            items.append(

                AuditPlanResponse(

                    id=audit.id,

                    name=audit.name,

                    description=audit.description,

                    auditor_id=audit.auditor.id,

                    auditor_name=audit.auditor.full_name,

                    frequency_unit=audit.frequency_unit,

                    frequency_interval=audit.frequency_interval,

                    start_date=audit.start_date,

                    end_date=audit.end_date,

                    next_run_date=audit.next_run_date,

                    status=audit.status,

                    created_at=audit.created_at

                )

            )

        return AuditPlanListResponse(

            items=items,

            total=total,

            page=page,

            size=size

        )

    @staticmethod
    def get_audit_by_id(
        audit_id: str,
        db: Session,
        current_user: User
    ):

        query = (
            db.query(AuditPlan)
            .join(User, AuditPlan.auditor_id == User.id)
            .filter(
                AuditPlan.id == audit_id,
                AuditPlan.is_active == True
            )
        )

        if current_user["role"] == "PLATFORM_ADMIN":

            pass

        elif current_user["role"] == "CLIENT_ADMIN":

            query = query.filter(
                AuditPlan.client_id == current_user["client_id"]
            )

        elif current_user["role"] == "AUDITOR":

            query = query.filter(
                AuditPlan.auditor_id == current_user["id"]
            )

        else:

            raise HTTPException(
                status_code=403,
                detail="Permission denied."
            )

        audit = query.first()

        if not audit:

            raise HTTPException(
                status_code=404,
                detail="Audit not found."
            )

        sessions = []

        for session in audit.audit_sessions:

            sessions.append(

                AuditSessionResponse(

                    id=session.id,

                    scheduled_date=session.scheduled_date,

                    started_at=session.started_at,

                    completed_at=session.completed_at,

                    status=session.status,

                    assigned_to=session.assigned_to,

                    conducted_by=session.conducted_by,

                    total_assets=session.total_assets,

                    audited_assets=session.audited_assets

                )

            )

        return AuditPlanResponse(

            id=audit.id,

            name=audit.name,

            description=audit.description,

            auditor_id=audit.auditor.id,

            auditor_name=audit.auditor.full_name,

            frequency_unit=audit.frequency_unit,

            frequency_interval=audit.frequency_interval,

            start_date=audit.start_date,

            end_date=audit.end_date,

            next_run_date=audit.next_run_date,

            status=audit.status,

            created_at=audit.created_at,

            sessions=sessions

        )

    @staticmethod
    def update_audit(
        audit_id: str,
        payload: AuditPlanUpdate,
        db: Session,
        current_user: User
    ):

        query = db.query(AuditPlan).filter(
            AuditPlan.id == audit_id,
            AuditPlan.is_active == True
        )

        if current_user["role"] == "PLATFORM_ADMIN":

            pass

        elif current_user["role"] == "CLIENT_ADMIN":

            query = query.filter(
                AuditPlan.client_id == current_user["client_id"]
            )

        else:

            raise HTTPException(
                status_code=403,
                detail="Permission denied."
            )

        audit = query.first()

        if not audit:

            raise HTTPException(
                status_code=404,
                detail="Audit not found."
            )

        if payload.auditor_id:

            auditor = (
                db.query(User)
                .filter(
                    User.id == payload.auditor_id,
                    User.client_id == audit.client_id,
                    User.is_active == True
                )
                .first()
            )

            if not auditor:

                raise HTTPException(
                    status_code=404,
                    detail="Auditor not found."
                )

            audit.auditor_id = payload.auditor_id

            pending_sessions = (
                db.query(AuditSession)
                .filter(
                    AuditSession.audit_plan_id == audit.id,
                    AuditSession.status == AuditSessionStatus.PENDING
                )
                .all()
            )

            for session in pending_sessions:

                session.assigned_to = payload.auditor_id

        if payload.name is not None:
            audit.name = payload.name

        if payload.description is not None:
            audit.description = payload.description

        if payload.frequency_unit is not None:
            audit.frequency_unit = payload.frequency_unit

        if payload.frequency_interval is not None:
            audit.frequency_interval = payload.frequency_interval

        if payload.start_date is not None:
            audit.start_date = payload.start_date

        if payload.end_date is not None:
            audit.end_date = payload.end_date

        if payload.status is not None:
            audit.status = payload.status

        if (
            payload.frequency_unit is not None or
            payload.frequency_interval is not None or
            payload.start_date is not None
        ):

            start_date = audit.start_date
            frequency_unit = audit.frequency_unit
            frequency_interval = audit.frequency_interval

            if frequency_unit == AuditFrequencyUnit.DAY:

                audit.next_run_date = (
                    start_date +
                    timedelta(days=frequency_interval)
                )

            elif frequency_unit == AuditFrequencyUnit.WEEK:

                audit.next_run_date = (
                    start_date +
                    timedelta(weeks=frequency_interval)
                )

            else:

                audit.next_run_date = (
                    start_date +
                    timedelta(days=30 * frequency_interval)
                )

        db.commit()

        db.refresh(audit)

        return AuditPlanResponse(

            id=audit.id,

            name=audit.name,

            description=audit.description,

            auditor_id=audit.auditor.id,

            auditor_name=audit.auditor.full_name,

            frequency_unit=audit.frequency_unit,

            frequency_interval=audit.frequency_interval,

            start_date=audit.start_date,

            end_date=audit.end_date,

            next_run_date=audit.next_run_date,

            status=audit.status,

            created_at=audit.created_at

        )

    @staticmethod
    def delete_audit(
        audit_id: str,
        db: Session,
        current_user: User
    ):

        query = db.query(AuditPlan).filter(
            AuditPlan.id == audit_id,
            AuditPlan.is_active == True
        )

        if current_user["role"] == "PLATFORM_ADMIN":

            pass

        elif current_user["role"] == "CLIENT_ADMIN":

            query = query.filter(
                AuditPlan.client_id == current_user["client_id"]
            )

        else:

            raise HTTPException(
                status_code=403,
                detail="Permission denied."
            )

        audit = query.first()

        if not audit:

            raise HTTPException(
                status_code=404,
                detail="Audit not found."
            )

        active_session = (
            db.query(AuditSession)
            .filter(
                AuditSession.audit_plan_id == audit.id,
                AuditSession.status == AuditSessionStatus.IN_PROGRESS
            )
            .first()
        )

        if active_session:

            raise HTTPException(
                status_code=400,
                detail="Cannot delete an audit with an active session."
            )

        audit.is_active = False

        db.commit()

        return {
            "message": "Audit deleted successfully."
        }

    @staticmethod
    def audit_dashboard(
        db: Session,
        current_user: User
    ):

        query = db.query(AuditPlan).filter(
            AuditPlan.is_active == True
        )

        if current_user["role"] == "PLATFORM_ADMIN":

            pass

        elif current_user["role"] == "CLIENT_ADMIN":

            query = query.filter(
                AuditPlan.client_id == current_user["client_id"]
            )

        else:

            raise HTTPException(
                status_code=403,
                detail="Permission denied."
            )

        audit_ids = [audit.id for audit in query.all()]

        total_audits = len(audit_ids)

        active_audits = (
            db.query(AuditPlan)
            .filter(
                AuditPlan.id.in_(audit_ids),
                AuditPlan.status == AuditPlanStatus.ACTIVE
            )
            .count()
        )

        completed_sessions = (
            db.query(AuditSession)
            .filter(
                AuditSession.audit_plan_id.in_(audit_ids),
                AuditSession.status == AuditSessionStatus.COMPLETED
            )
            .count()
        )

        pending_sessions = (
            db.query(AuditSession)
            .filter(
                AuditSession.audit_plan_id.in_(audit_ids),
                AuditSession.status == AuditSessionStatus.PENDING
            )
            .count()
        )

        in_progress_sessions = (
            db.query(AuditSession)
            .filter(
                AuditSession.audit_plan_id.in_(audit_ids),
                AuditSession.status == AuditSessionStatus.IN_PROGRESS
            )
            .count()
        )

        total_assets = (
            db.query(AuditResult)
            .join(AuditSession)
            .filter(
                AuditSession.audit_plan_id.in_(audit_ids)
            )
            .count()
        )

        audited_assets = (
            db.query(AuditResult)
            .join(AuditSession)
            .filter(
                AuditSession.audit_plan_id.in_(audit_ids),
                AuditResult.status != AuditResultStatus.PENDING
            )
            .count()
        )

        return AuditDashboardResponse(

            total_audits=total_audits,

            active_audits=active_audits,

            completed_sessions=completed_sessions,

            pending_sessions=pending_sessions,

            in_progress_sessions=in_progress_sessions,

            total_assets=total_assets,

            audited_assets=audited_assets

        )

    @staticmethod
    def audit_history(
        db: Session,
        current_user: User,
        page: int = 1,
        size: int = 10,
    ):

        query = (
            db.query(AuditSession)
            .join(AuditPlan)
            .join(User, AuditSession.assigned_to == User.id)
            .filter(
                AuditSession.status == AuditSessionStatus.COMPLETED,
                AuditPlan.is_active == True
            )
        )

        if current_user["role"] == "PLATFORM_ADMIN":

            pass

        elif current_user["role"] == "CLIENT_ADMIN":

            query = query.filter(
                AuditPlan.client_id == current_user["client_id"]
            )

        else:

            query = query.filter(
                AuditSession.assigned_to == current_user["id"]
            )

        total = query.count()

        sessions = (
            query.order_by(AuditSession.completed_at.desc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )

        items = []

        for session in sessions:

            items.append(

                AuditSessionResponse(

                    id=session.id,

                    audit_plan_id=session.audit_plan.id,

                    audit_name=session.audit_plan.name,

                    scheduled_date=session.scheduled_date,

                    started_at=session.started_at,

                    completed_at=session.completed_at,

                    assigned_to=session.assigned_to,

                    assigned_to_name=session.assigned_user.full_name,

                    conducted_by=session.conducted_by,

                    total_assets=session.total_assets,

                    audited_assets=session.audited_assets,

                    status=session.status

                )

            )

        return AuditSessionListResponse(

            items=items,

            total=total,

            page=page,

            size=size

        )

    # -------------------- HELPER METHODS --------------------
    
    @staticmethod
    def get_audit_session(
        db: Session,
        audit_id: str,
        current_user: User
    ) -> AuditSession:
        """
        Get and verify the audit session exists and is assigned to the user.
        
        Args:
            db: Database session
            audit_id: The audit plan ID
            current_user: The authenticated user
            
        Returns:
            AuditSession if valid
            
        Raises:
            HTTPException: If audit not found or user not authorized
        """
        session = (
            db.query(AuditSession)
            .join(AuditPlan)
            .filter(
                AuditPlan.id == audit_id,
                AuditSession.assigned_to == current_user["id"]
            )
            .first()
        )
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit not found or you don't have access to it."
            )
        
        return session

    @staticmethod
    def get_audit_assets(
        db: Session,
        audit_id: str
    ) -> Dict[str, Asset]:
        """
        Get all assets that belong to an audit plan.
        
        Args:
            db: Database session
            audit_id: The audit plan ID
            
        Returns:
            Dictionary mapping asset_id to Asset objects
        """
        targets = (
            db.query(AuditTarget)
            .filter(
                AuditTarget.audit_plan_id == audit_id
            )
            .all()
        )
        
        assets_map = {}
        
        for target in targets:
            assets = []
            
            if target.target_type == AuditTargetType.ASSET:
                assets = (
                    db.query(Asset)
                    .filter(
                        Asset.id == target.target_id,
                        Asset.is_active == True
                    )
                    .all()
                )
                
            elif target.target_type == AuditTargetType.LOCATION:
                assets = (
                    db.query(Asset)
                    .filter(
                        Asset.location_id == target.target_id,
                        Asset.is_active == True
                    )
                    .all()
                )
                
            elif target.target_type == AuditTargetType.DEPARTMENT:
                assets = (
                    db.query(Asset)
                    .filter(
                        Asset.department_id == target.target_id,
                        Asset.is_active == True
                    )
                    .all()
                )
                
            elif target.target_type == AuditTargetType.CATEGORY:
                assets = (
                    db.query(Asset)
                    .filter(
                        Asset.category_id == target.target_id,
                        Asset.is_active == True
                    )
                    .all()
                )
            
            for asset in assets:
                assets_map[asset.id] = asset
        
        return assets_map

    @staticmethod
    def get_asset_and_verify(
        db: Session,
        asset_id: str,
        audit_id: str
    ) -> Asset:
        """
        Get asset and verify it exists, is active, and belongs to the audit.
        
        Args:
            db: Database session
            asset_id: The asset ID
            audit_id: The audit plan ID
            
        Returns:
            Asset if valid
            
        Raises:
            HTTPException: If asset not found or not part of audit
        """
        # Find the asset
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
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset not found."
            )
        
        # Verify asset belongs to this audit
        audit_assets = AuditService.get_audit_assets(db, audit_id)
        
        if asset.id not in audit_assets:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This asset is not part of this audit."
            )
        
        return asset

    @staticmethod
    def _get_location_status(audit_status: AuditResultStatus) -> str:
        """
        Map audit result status to location status.
        
        Database location_status column expects:
        - 'VERIFIED'
        - 'NEARBY' 
        - 'OUTSIDE_GEOFENCE'
        - 'LOCATION_UNKNOWN'
        
        This mapping ensures the correct values are saved.
        """
        mapping = {
            AuditResultStatus.IN_PLACE: "VERIFIED",
            AuditResultStatus.DISLOCATED: "OUTSIDE_GEOFENCE",
            AuditResultStatus.NOT_FOUND: "LOCATION_UNKNOWN",
            AuditResultStatus.LOST: "LOCATION_UNKNOWN",
            AuditResultStatus.PENDING: "LOCATION_UNKNOWN",
        }
        return mapping.get(audit_status, "LOCATION_UNKNOWN")

    # -------------------- MAIN ENDPOINT METHODS --------------------

    @staticmethod
    def get_audit_details(
        db: Session,
        audit_id: str,
        current_user: User
    ) -> AuditDetailsResponse:
        """
        Get detailed information about a specific audit session.
        """
        
        # Get the audit session
        session = AuditService.get_audit_session(db, audit_id, current_user)
        
        # Get all assets in this audit
        assets_map = AuditService.get_audit_assets(db, audit_id)
        
        # Find audited assets for this session (non-PENDING status)
        audited_asset_ids = {
            row.asset_id
            for row in db.query(AuditResult.asset_id)
            .filter(
                AuditResult.audit_session_id == session.id,
                AuditResult.status != AuditResultStatus.PENDING
            )
            .all()
        }
        
        # Build asset response list
        asset_list = []
        
        for asset in assets_map.values():
            location_name = None
            if asset.location:
                location_name = asset.location.name
            
            asset_list.append(
                AuditAssetResponse(
                    asset_id=asset.id,
                    asset_name=asset.name,
                    serial_number=asset.serial_number,
                    qr_code_url=asset.qr_code_url,
                    location=location_name,
                    audit_status=(
                        "AUDITED"
                        if asset.id in audited_asset_ids
                        else "PENDING"
                    )
                )
            )
        
        # Calculate completion percentage
        completion_percentage = 0.0
        
        if session.total_assets and session.total_assets > 0:
            completion_percentage = round(
                (session.audited_assets / session.total_assets) * 100,
                2
            )
        
        # Return the complete response
        return AuditDetailsResponse(
            audit_id=session.audit_plan.id,
            session_id=session.id,
            audit_name=session.audit_plan.name,
            description=session.audit_plan.description,
            status=session.status,
            scheduled_date=session.scheduled_date,
            start_date=session.audit_plan.start_date,
            end_date=session.audit_plan.end_date,
            total_assets=session.total_assets,
            audited_assets=session.audited_assets,
            completion_percentage=completion_percentage,
            assets=asset_list
        )

    @staticmethod
    def get_my_audits_simple(
        db: Session,
        current_user: User
    ):
        print("called")
        sessions = (
            db.query(AuditSession)
            .join(AuditPlan)
            .filter(
                AuditSession.assigned_to == current_user["id"]
            )
            .all()
        )
        response = []
        for session in sessions:
            percentage = 0
            if session.total_assets:
                percentage = round(
                    (session.audited_assets / session.total_assets) * 100,
                    2
                )

            response.append(
                MyAuditResponse(
                    audit_id=session.audit_plan.id,
                    session_id=session.id,
                    audit_name=session.audit_plan.name,
                    status=session.status,
                    start_date=session.audit_plan.start_date,
                    end_date=session.audit_plan.end_date,
                    scheduled_date=session.scheduled_date,
                    total_assets=session.total_assets,
                    audited_assets=session.audited_assets,
                    completion_percentage=percentage
                )
            )
        return response

    @staticmethod
    def start_audit_session(
        session_id: str,
        db: Session,
        current_user: User
    ):

        session = (
            db.query(AuditSession)
            .filter(
                AuditSession.id == session_id
            )
            .first()
        )

        if not session:

            raise HTTPException(
                status_code=404,
                detail="Audit session not found."
            )

        # Check if the current user is the assigned auditor
        if session.assigned_to != current_user["id"]:

            raise HTTPException(
                status_code=403,
                detail="This audit is not assigned to you."
            )

        if session.status != AuditSessionStatus.PENDING:

            raise HTTPException(
                status_code=400,
                detail="Audit session has already started."
            )

        audit_plan = session.audit_plan

        # Use the consolidated helper method
        assets_map = AuditService.get_audit_assets(db, audit_plan.id)
        assets = list(assets_map.values())

        session.total_assets = len(assets)
        session.audited_assets = 0

        session.status = AuditSessionStatus.IN_PROGRESS

        session.started_at = datetime.utcnow()

        session.conducted_by = current_user["id"]

        for asset in assets:

            result = AuditResult(

                audit_session_id=session.id,

                asset_id=asset.id,

                expected_location_id=asset.location_id,

                expected_latitude=asset.current_latitude,

                expected_longitude=asset.current_longitude,

                status=AuditResultStatus.PENDING

            )

            db.add(result)

        db.commit()

        db.refresh(session)

        return AuditSessionResponse(

            id=session.id,

            audit_plan_id=session.audit_plan.id,

            audit_name=session.audit_plan.name,

            scheduled_date=session.scheduled_date,

            started_at=session.started_at,

            completed_at=session.completed_at,

            assigned_to=session.assigned_to,

            conducted_by=session.conducted_by,

            total_assets=session.total_assets,

            audited_assets=session.audited_assets,

            status=session.status

        )

    @staticmethod
    def start_audit_session_by_plan(
        audit_id: str,
        db: Session,
        current_user: User
    ):
        """
        Start an audit session using the audit plan ID.
        
        This finds the active/pending session for the given audit plan
        and starts it.
        """
        
        # Find the active/pending session for this audit plan
        session = (
            db.query(AuditSession)
            .join(AuditPlan)
            .filter(
                AuditPlan.id == audit_id,
                AuditSession.assigned_to == current_user["id"],
                AuditSession.status == AuditSessionStatus.PENDING
            )
            .first()
        )
        
        if not session:
            raise HTTPException(
                status_code=404,
                detail="No pending audit session found for this audit."
            )
        
        # Use the existing start_audit_session method
        return AuditService.start_audit_session(
            session_id=session.id,
            db=db,
            current_user=current_user
        )

    @staticmethod
    def scan_asset(
        db: Session,
        audit_id: str,
        asset_id: str,
        current_user: User
    ) -> ScanAssetResponse:
        """
        Validate a scanned asset.

        This endpoint validates that the scanned asset:
        - Belongs to the audit
        - Exists and is active
        - Has not already been audited

        Returns asset details for verification before submitting the audit result.
        """
        
        # Verify audit session exists and is active
        session = AuditService.get_audit_session(db, audit_id, current_user)
        
        # Check if session is active
        if session.status != AuditSessionStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Audit session is not active."
            )
        
        # Verify asset belongs to audit
        asset = AuditService.get_asset_and_verify(db, asset_id, audit_id)
        
        # Check if already audited
        audit_result = (
            db.query(AuditResult)
            .filter(
                AuditResult.audit_session_id == session.id,
                AuditResult.asset_id == asset.id
            )
            .first()
        )
        
        if not audit_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset not found in this audit."
            )
        
        if audit_result.status != AuditResultStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Asset has already been audited."
            )
        
        # Return asset details
        return ScanAssetResponse(
            asset_id=asset.id,
            asset_name=asset.name,
            serial_number=asset.serial_number,
            qr_code_url=asset.qr_code_url,
            location=asset.location.name if asset.location else None,
            expected_condition=asset.asset_condition,
            already_audited=False  # Since we passed the PENDING check
        )

    @staticmethod
    def submit_asset_audit(
        db: Session,
        audit_id: str,
        asset_id: str,
        status: str,
        condition_status: str,
        quantity_found: int,
        remarks: str | None,
        audit_latitude: float,
        audit_longitude: float,
        photo: UploadFile | None,
        current_user: User
    ) -> SubmitAssetAuditResponse:
        """
        Submit audit results for a specific asset during an audit.
        
        This is the core endpoint for the mobile audit flow where auditors
        submit their findings for each asset.
        """
        
        # Step 1: Verify audit session exists and user is assigned
        session = AuditService.get_audit_session(db, audit_id, current_user)
        
        # Step 2: Verify session is active
        if session.status != AuditSessionStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Audit session is not active."
            )
        
        # Step 3: Verify asset exists, is active, and belongs to audit
        asset = AuditService.get_asset_and_verify(db, asset_id, audit_id)
        
        # Step 4: Get the existing AuditResult (created during start_audit_session)
        audit_result = (
            db.query(AuditResult)
            .filter(
                AuditResult.audit_session_id == session.id,
                AuditResult.asset_id == asset.id
            )
            .first()
        )
        
        if not audit_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset not found in this audit."
            )
        
        # Step 5: Check if already audited (not PENDING)
        if audit_result.status != AuditResultStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Asset has already been audited."
            )
        
        # Step 6: Convert status string to enum for mapping
        try:
            status_enum = AuditResultStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid audit status: {status}"
            )
        
        # Step 7: Update the existing AuditResult with findings
        audit_result.status = status
        audit_result.condition_status = condition_status
        audit_result.quantity_found = quantity_found
        audit_result.remarks = remarks
        audit_result.audit_latitude = audit_latitude
        audit_result.audit_longitude = audit_longitude
        
        # Step 8: Set location_status using the helper method (FIXED)
        audit_result.location_status = AuditService._get_location_status(status_enum)
        
        # Step 9: Handle photo upload if provided
        if photo:
            try:
                # Generate a unique filename
                file_extension = photo.filename.split('.')[-1] if photo.filename else 'jpg'
                filename = f"audit_{audit_id}_{asset_id}_{uuid.uuid4().hex[:8]}.{file_extension}"
                
                print(f"UPLOADING AUDIT PHOTO: {filename}")
                
                # Upload to Cloudinary
                upload_result = cloudinary.uploader.upload(
                    photo.file,
                    folder=f"assetiq/{asset.client_id}/audits/{audit_id}",
                    public_id=filename,
                    resource_type="image",
                    overwrite=True
                )
                
                # Get the secure URL
                image_url = upload_result.get('secure_url')
                
                if not image_url:
                    raise HTTPException(
                        status_code=500,
                        detail="Cloudinary did not return an image URL"
                    )
                
                print(f"AUDIT PHOTO UPLOADED: {image_url}")
                
                # Save the URL to audit result
                audit_result.photo_url = image_url
                
            except HTTPException:
                raise
            except Exception as error:
                print(f"AUDIT PHOTO UPLOAD FAILED: {str(error)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to upload audit photo: {str(error)}"
                )
        
        audit_result.audited_by = current_user["id"]
        audit_result.audited_at = datetime.utcnow()
        
        # Step 10: Increment audited_assets count
        session.audited_assets += 1
        
        # Step 11: Commit changes
        db.commit()
        
        # Step 12: Refresh for latest data
        db.refresh(audit_result)
        db.refresh(session)
        
        # Step 13: Calculate remaining assets and completion percentage
        remaining_assets = session.total_assets - session.audited_assets
        
        completion_percentage = 0.0
        if session.total_assets and session.total_assets > 0:
            completion_percentage = round(
                (session.audited_assets / session.total_assets) * 100,
                2
            )
        
        # Step 14: Check if all assets are audited
        is_complete = session.audited_assets >= session.total_assets
        
        # Step 15: Return response
        return SubmitAssetAuditResponse(
            message="Asset audited successfully.",
            audit_id=session.audit_plan.id,
            session_id=session.id,
            asset_id=asset.id,
            asset_name=asset.name,
            audited_assets=session.audited_assets,
            total_assets=session.total_assets,
            remaining_assets=remaining_assets,
            completion_percentage=completion_percentage,
            is_complete=is_complete
        )

    @staticmethod
    def complete_audit_session_manual(
        db: Session,
        audit_id: str,
        current_user: User
    ) -> dict:
        """
        Manually complete an audit session.
        
        This endpoint should be called when:
        1. All assets have been audited (is_complete = true)
        2. The auditor has reviewed and confirmed the audit
        
        The audit will be marked as COMPLETED and cannot be modified further.
        """
        
        # Step 1: Verify audit session exists and user is assigned
        session = AuditService.get_audit_session(db, audit_id, current_user)
        
        # Step 2: Verify session is in progress
        if session.status != AuditSessionStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Audit session is not active. Current status: {session.status}"
            )
        
        # Step 3: Check if all assets have been audited
        if session.audited_assets < session.total_assets:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot complete audit. Only {session.audited_assets} out of {session.total_assets} assets have been audited."
            )
        
        # Step 4: Complete the audit
        session.status = AuditSessionStatus.COMPLETED
        session.completed_at = datetime.utcnow()
        
        # Update next run date for recurring audits
        audit_plan = session.audit_plan
        if audit_plan.frequency_unit == AuditFrequencyUnit.DAY:
            audit_plan.next_run_date += timedelta(
                days=audit_plan.frequency_interval
            )
        elif audit_plan.frequency_unit == AuditFrequencyUnit.WEEK:
            audit_plan.next_run_date += timedelta(
                weeks=audit_plan.frequency_interval
            )
        else:
            audit_plan.next_run_date += timedelta(
                days=30 * audit_plan.frequency_interval
            )
        
        # Create next session for recurring audits
        new_session = AuditSession(
            audit_plan_id=audit_plan.id,
            assigned_to=audit_plan.auditor_id,
            scheduled_date=audit_plan.next_run_date,
            status=AuditSessionStatus.PENDING,
            total_assets=0,
            audited_assets=0
        )
        db.add(new_session)
        
        db.commit()
        db.refresh(session)
        
        # Step 5: Return response
        return {
            "success": True,
            "message": "Audit completed successfully.",
            "audit_id": session.audit_plan.id,
            "session_id": session.id,
            "status": session.status,
            "completed_at": session.completed_at,
            "total_assets": session.total_assets,
            "audited_assets": session.audited_assets,
            "completion_percentage": 100.0
        }

    @staticmethod
    def get_audit_summary(
        db: Session,
        audit_id: str,
        current_user: User
    ) -> AuditSummaryResponse:
        """
        Get summary statistics for an audit.
        """

        # Get audit session assigned to the current user
        session = AuditService.get_audit_session(
            db=db,
            audit_id=audit_id,
            current_user=current_user
        )

        results = (
            db.query(AuditResult)
            .filter(
                AuditResult.audit_session_id == session.id
            )
            .all()
        )

        total_assets = session.total_assets
        audited_assets = session.audited_assets
        remaining_assets = total_assets - audited_assets

        completion_percentage = 0.0
        if total_assets > 0:
            completion_percentage = round(
                (audited_assets / total_assets) * 100,
                2
            )

        in_place = 0
        dislocated = 0
        not_found = 0
        lost = 0

        for result in results:
            if result.status == AuditResultStatus.IN_PLACE:
                in_place += 1
            elif result.status == AuditResultStatus.DISLOCATED:
                dislocated += 1
            elif result.status == AuditResultStatus.NOT_FOUND:
                not_found += 1
            elif result.status == AuditResultStatus.LOST:
                lost += 1

        return AuditSummaryResponse(
            audit_id=session.audit_plan.id,
            session_id=session.id,
            audit_name=session.audit_plan.name,
            status=session.status,
            total_assets=total_assets,
            audited_assets=audited_assets,
            remaining_assets=remaining_assets,
            completion_percentage=completion_percentage,
            in_place=in_place,
            dislocated=dislocated,
            not_found=not_found,
            lost=lost,
        )

    @staticmethod
    def get_asset_details(
        db: Session,
        audit_id: str,
        asset_id: str,
        current_user: User
    ) -> AuditAssetDetailsResponse:
        """
        Get detailed information about a specific asset within an audit.
        
        This endpoint returns comprehensive asset details including:
        - Basic asset information (ID, name, code, serial number)
        - Category, department, and location
        - Manufacturer and model
        - Expected quantity and condition
        - Image URL
        
        Used by the mobile app after a successful scan to display asset details
        before the auditor submits the audit result.
        """
        
        # Verify audit belongs to current user
        AuditService.get_audit_session(
            db=db,
            audit_id=audit_id,
            current_user=current_user
        )

        # Verify asset belongs to audit
        asset = AuditService.get_asset_and_verify(
            db=db,
            asset_id=asset_id,
            audit_id=audit_id
        )

        return AuditAssetDetailsResponse(
            asset_id=asset.id,
            asset_name=asset.name,
            asset_code=getattr(asset, "asset_code", None),
            serial_number=asset.serial_number,
            category=asset.category.name if asset.category else None,
            department=asset.department.name if asset.department else None,
            location=asset.location.name if asset.location else None,
            manufacturer=getattr(asset, "manufacturer", None),
            model=getattr(asset, "model", None),
            expected_quantity=getattr(asset, "quantity", None),
            expected_condition=str(asset.asset_condition) if asset.asset_condition else None,
            image_url=getattr(asset, "image_url", None)
        )