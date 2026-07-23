from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

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
        current_user
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
        current_user,
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
        current_user
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
        current_user
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
        current_user
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
    def get_my_audits(
        db: Session,
        current_user,
        page: int = 1,
        size: int = 10,
        status: AuditSessionStatus | None = None,
    ):

        query = (
            db.query(AuditSession)
            .join(AuditPlan)
            .filter(
                AuditSession.assigned_to == current_user["id"],
                AuditPlan.is_active == True
            )
        )

        if status:

            query = query.filter(
                AuditSession.status == status
            )

        total = query.count()

        sessions = (
            query.order_by(AuditSession.scheduled_date.desc())
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

    @staticmethod
    def start_audit_session(
        session_id: str,
        db: Session,
        current_user
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

        assets = AuditService._get_assets_from_targets(
            audit_plan=audit_plan,
            db=db
        )

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
    def submit_asset_audit(
        session_id: str,
        asset_id: str,
        payload: AuditResultRequest,
        db: Session,
        current_user
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

        if session.status != AuditSessionStatus.IN_PROGRESS:

            raise HTTPException(
                status_code=400,
                detail="Audit session is not in progress."
            )

        result = (
            db.query(AuditResult)
            .filter(
                AuditResult.audit_session_id == session_id,
                AuditResult.asset_id == asset_id
            )
            .first()
        )

        if not result:

            raise HTTPException(
                status_code=404,
                detail="Asset not found in this audit."
            )

        if result.status != AuditResultStatus.PENDING:

            raise HTTPException(
                status_code=400,
                detail="Asset already audited."
            )

        result.audit_latitude = payload.audit_latitude
        result.audit_longitude = payload.audit_longitude
        result.actual_location_id = payload.actual_location_id

        result.condition = payload.condition
        result.remarks = payload.remarks
        result.image_url = payload.image_url

        result.location_status = payload.location_status
        result.status = AuditResultStatus.COMPLETED

        result.audited_at = datetime.utcnow()

        session.audited_assets += 1

        db.commit()

        db.refresh(result)

        return AuditResultResponse(

            id=result.id,

            asset_id=result.asset_id,

            asset_name=result.asset.asset_name,

            expected_location_id=result.expected_location_id,

            actual_location_id=result.actual_location_id,

            expected_latitude=result.expected_latitude,

            expected_longitude=result.expected_longitude,

            audit_latitude=result.audit_latitude,

            audit_longitude=result.audit_longitude,

            location_status=result.location_status,

            condition=result.condition,

            remarks=result.remarks,

            image_url=result.image_url,

            status=result.status,

            audited_at=result.audited_at

        )

    @staticmethod
    def complete_audit_session(
        session_id: str,
        db: Session,
        current_user
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

        if session.status != AuditSessionStatus.IN_PROGRESS:

            raise HTTPException(
                status_code=400,
                detail="Audit session is not in progress."
            )

        pending_assets = (
            db.query(AuditResult)
            .filter(
                AuditResult.audit_session_id == session.id,
                AuditResult.status == AuditResultStatus.PENDING
            )
            .count()
        )

        if pending_assets > 0:

            raise HTTPException(
                status_code=400,
                detail="All assets must be audited before completing the audit."
            )

        session.status = AuditSessionStatus.COMPLETED

        session.completed_at = datetime.utcnow()

        audit_plan = session.audit_plan

        # Update next run date
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

        # Create next session
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
    def _get_assets_from_targets(
        audit_plan: AuditPlan,
        db: Session
    ) -> list[Asset]:
        """Helper method to get all assets from audit targets."""
        asset_ids = set()

        targets = (
            db.query(AuditTarget)
            .filter(
                AuditTarget.audit_plan_id == audit_plan.id
            )
            .all()
        )

        for target in targets:

            # ---------------------------------
            # Individual Asset
            # ---------------------------------

            if target.target_type == AuditTargetType.ASSET:

                asset = (
                    db.query(Asset)
                    .filter(
                        Asset.id == target.target_id,
                        Asset.is_active == True
                    )
                    .first()
                )

                if asset:
                    asset_ids.add(asset.id)

            # ---------------------------------
            # Category
            # ---------------------------------

            elif target.target_type == AuditTargetType.CATEGORY:

                assets = (
                    db.query(Asset)
                    .filter(
                        Asset.category_id == target.target_id,
                        Asset.client_id == audit_plan.client_id,
                        Asset.is_active == True
                    )
                    .all()
                )

                for asset in assets:
                    asset_ids.add(asset.id)

            # ---------------------------------
            # Department
            # ---------------------------------

            elif target.target_type == AuditTargetType.DEPARTMENT:

                assets = (
                    db.query(Asset)
                    .filter(
                        Asset.department_id == target.target_id,
                        Asset.client_id == audit_plan.client_id,
                        Asset.is_active == True
                    )
                    .all()
                )

                for asset in assets:
                    asset_ids.add(asset.id)

            # ---------------------------------
            # Location
            # ---------------------------------

            elif target.target_type == AuditTargetType.LOCATION:

                assets = (
                    db.query(Asset)
                    .filter(
                        Asset.location_id == target.target_id,
                        Asset.client_id == audit_plan.client_id,
                        Asset.is_active == True
                    )
                    .all()
                )

                for asset in assets:
                    asset_ids.add(asset.id)

        if not asset_ids:
            return []

        return (
            db.query(Asset)
            .filter(
                Asset.id.in_(asset_ids)
            )
            .all()
        )

    @staticmethod
    def audit_dashboard(
        db: Session,
        current_user
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
                AuditResult.status == AuditResultStatus.COMPLETED
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
        current_user,
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
    @staticmethod
    def get_session_assets(
    session_id: str,
    db: Session,
    current_user
):
        session = (
        db.query(AuditSession)
        .filter(AuditSession.id == session_id)
        .first()
    )
        if not session:
            raise HTTPException(
            status_code=404,
            detail="Audit session not found."
        )
        if session.assigned_to != current_user["id"]:
            raise HTTPException(
            status_code=403,
            detail="Permission denied."
        )
        results = (
        db.query(AuditResult)
        .join(Asset)
        .filter(
            AuditResult.audit_session_id == session_id
        )
        .all()
        )
        return [
        AuditResultResponse(
            asset_id=result.asset_id,
            asset_name=result.asset.name,
            serial_number=result.asset.serial_number,
            
            status=result.status,
            condition_status=result.condition_status,
            
            quantity_expected=result.quantity_expected,
            quantity_found=result.quantity_found,
            
            remarks=result.remarks,
            photo_url=result.photo_url,
            
            expected_location_id=result.expected_location_id,
            expected_latitude=result.expected_latitude,
            expected_longitude=result.expected_longitude,
            
            audit_latitude=result.audit_latitude,
            audit_longitude=result.audit_longitude,
            
            location_status=result.location_status,
            
            audited_by=result.audited_by,
            audited_at=result.audited_at,
        )
        for result in results
    ]
    def get_my_audits(
    db: Session,
    current_user: User
):
        sessions = (
        db.query(AuditSession)
        .join(AuditPlan)
        .filter(
            AuditSession.assigned_to == current_user.id
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