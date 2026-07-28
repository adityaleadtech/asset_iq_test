from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from fastapi import HTTPException, status, UploadFile
from sqlalchemy.orm import Session
import cloudinary.uploader
import uuid

from app.models.asset import Asset
from app.models.auditplan import AuditPlan
from app.models.auditsession import AuditSession
from app.models.audittaget import AuditTarget
from app.models.AuditResult import AuditResult
from app.models.location import Location
from app.models.departments import Department
from app.models.asset_categories import AssetCategory
from app.models.users import User
from app.models.clients import Client

from app.schemas.Audit import (
    AuditPlanCreate,
    AuditPlanUpdate,
    AuditPlanResponse,
    AuditPlanListResponse,
    AuditSessionResponse,
    AuditSessionListResponse,
    AuditDashboardResponse,
    MyAuditResponse,
    AuditDetailsResponse,
    AuditAssetResponse,
    ScanAssetResponse,
    ScanAssetRequest,
    SubmitAssetAuditResponse,
    AuditAssetDetailsResponse,
    AuditSummaryResponse,
    AuditReviewResponse,
    AuditReviewAsset,
    AuditReportResponse,
    AuditReportInformation,
    AuditInformation,
    AuditSummary,
    AssetVerificationDetail,
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
    def _ensure_user_object(current_user: Union[User, dict]) -> User:
        """Helper method to ensure we have a User object, not a dict"""
        if isinstance(current_user, dict):
            user = User()
            user.id = current_user.get("id")
            user.role = current_user.get("role")
            user.client_id = current_user.get("client_id")
            user.full_name = current_user.get("full_name")
            user.email = current_user.get("email")
            user.is_active = current_user.get("is_active", True)
            return user
        return current_user

    @staticmethod
    def _generate_schedule_dates(
        start_date: datetime,
        end_date: datetime,
        frequency_unit: str,
        frequency_interval: int
    ) -> List[datetime]:
        """Generate dates between start and end based on frequency"""
        dates = []
        current = start_date
        
        while current <= end_date:
            dates.append(current)
            
            if frequency_unit == AuditFrequencyUnit.DAY:
                current += timedelta(days=frequency_interval)
            elif frequency_unit == AuditFrequencyUnit.WEEK:
                current += timedelta(weeks=frequency_interval)
            else:  # MONTH
                current += timedelta(days=30 * frequency_interval)
        
        return dates

    @staticmethod
    def create_audit(
        payload: AuditPlanCreate,
        db: Session,
        current_user: Union[User, dict]
    ):
        current_user = AuditService._ensure_user_object(current_user)
        
        try:
            if current_user.role == "ADMIN":
                if not payload.client_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="client_id is required for platform admin"
                    )
                client_id = payload.client_id
            else:
                client_id = current_user.client_id
                if not client_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="User not associated with a client"
                    )

            client = db.query(Client).filter(
                Client.id == client_id,
                Client.is_active == True
            ).first()
            
            if not client:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Client not found"
                )

            auditor = db.query(User).filter(
                User.id == payload.auditor_id,
                User.client_id == client_id,
                User.is_active == True
            ).first()
            
            if not auditor:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Auditor not found"
                )

            seen = set()
            for target in payload.targets:
                key = (target.target_type, target.target_id)
                if key in seen:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Duplicate audit target"
                    )
                seen.add(key)

            for target in payload.targets:
                if target.target_type == AuditTargetType.LOCATION:
                    exists = db.query(Location).filter(
                        Location.id == target.target_id,
                        Location.client_id == client_id,
                        Location.is_active == True
                    ).first()
                    if not exists:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Location {target.target_id} not found"
                        )
                elif target.target_type == AuditTargetType.DEPARTMENT:
                    exists = db.query(Department).filter(
                        Department.id == target.target_id,
                        Department.is_active == True
                    ).first()
                    if not exists:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Department {target.target_id} not found"
                        )
                elif target.target_type == AuditTargetType.CATEGORY:
                    exists = db.query(AssetCategory).filter(
                        AssetCategory.id == target.target_id,
                        AssetCategory.is_active == True
                    ).first()
                    if not exists:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Category {target.target_id} not found"
                        )
                elif target.target_type == AuditTargetType.ASSET:
                    exists = db.query(Asset).filter(
                        Asset.id == target.target_id,
                        Asset.client_id == client_id,
                        Asset.is_active == True
                    ).first()
                    if not exists:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Asset {target.target_id} not found"
                        )

            audit_plan = AuditPlan(
                client_id=client_id,
                name=payload.name,
                description=payload.description,
                auditor_id=payload.auditor_id,
                frequency_unit=payload.frequency_unit,
                frequency_interval=payload.frequency_interval,
                start_date=payload.start_date,
                end_date=payload.end_date,
                next_run_date=payload.start_date,
                status=AuditPlanStatus.ACTIVE,
                created_by=current_user.id,
                is_active=True
            )
            db.add(audit_plan)
            db.flush()

            for target in payload.targets:
                audit_target = AuditTarget(
                    audit_plan_id=audit_plan.id,
                    target_type=target.target_type,
                    target_id=target.target_id
                )
                db.add(audit_target)

            scheduled_dates = AuditService._generate_schedule_dates(
                start_date=payload.start_date,
                end_date=payload.end_date,
                frequency_unit=payload.frequency_unit,
                frequency_interval=payload.frequency_interval
            )

            sessions_created = 0
            for scheduled_date in scheduled_dates:
                audit_session = AuditSession(
                    audit_plan_id=audit_plan.id,
                    assigned_to=payload.auditor_id,
                    scheduled_date=scheduled_date,
                    status=AuditSessionStatus.PENDING,
                    total_assets=0,
                    audited_assets=0
                )
                db.add(audit_session)
                sessions_created += 1

            db.commit()
            db.refresh(audit_plan)

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
                created_at=audit_plan.created_at,
                sessions_count=sessions_created
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
        current_user: Union[User, dict],
        page: int = 1,
        size: int = 10,
        search: Optional[str] = None,
        status: Optional[str] = None
    ):
        current_user = AuditService._ensure_user_object(current_user)
        
        query = db.query(AuditPlan).filter(AuditPlan.is_active == True)
        
        if current_user.role == "ADMIN":
            pass
        elif current_user.role == "CLIENT_ADMIN":
            query = query.filter(AuditPlan.client_id == current_user.client_id)
        else:
            query = query.filter(AuditPlan.auditor_id == current_user.id)
        
        if search:
            query = query.filter(AuditPlan.name.ilike(f"%{search}%"))
        
        if status:
            query = query.filter(AuditPlan.status == status)
        
        total = query.count()
        query = query.order_by(AuditPlan.created_at.desc())
        query = query.offset((page - 1) * size).limit(size)
        
        audits = query.all()
        
        items = []
        for audit in audits:
            items.append(
                AuditPlanResponse(
                    id=audit.id,
                    name=audit.name,
                    description=audit.description,
                    auditor_id=audit.auditor_id,
                    auditor_name=audit.auditor.full_name if audit.auditor else "",
                    frequency_unit=audit.frequency_unit,
                    frequency_interval=audit.frequency_interval,
                    start_date=audit.start_date,
                    end_date=audit.end_date,
                    next_run_date=audit.next_run_date,
                    status=audit.status,
                    created_at=audit.created_at,
                    sessions_count=len(audit.sessions) if audit.sessions else 0
                )
            )
        
        return AuditPlanListResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size if total > 0 else 0
        )

    @staticmethod
    def audit_dashboard(
        db: Session,
        current_user: Union[User, dict]
    ) -> AuditDashboardResponse:
        current_user = AuditService._ensure_user_object(current_user)
        
        query = db.query(AuditPlan).filter(AuditPlan.is_active == True)
        
        if current_user.role == "ADMIN":
            pass
        elif current_user.role == "CLIENT_ADMIN":
            query = query.filter(AuditPlan.client_id == current_user.client_id)
        else:
            query = query.filter(AuditPlan.auditor_id == current_user.id)
        
        audits = query.all()
        total_audits = len(audits)
        active_audits = sum(1 for a in audits if a.status == "ACTIVE")
        
        sessions = db.query(AuditSession).join(AuditPlan).filter(AuditPlan.is_active == True)
        
        if current_user.role == "CLIENT_ADMIN":
            sessions = sessions.filter(AuditPlan.client_id == current_user.client_id)
        elif current_user.role != "ADMIN":
            sessions = sessions.filter(AuditSession.assigned_to == current_user.id)
        
        all_sessions = sessions.all()
        completed_sessions = sum(1 for s in all_sessions if s.status == "COMPLETED")
        pending_sessions = sum(1 for s in all_sessions if s.status == "PENDING")
        in_progress_sessions = sum(1 for s in all_sessions if s.status == "IN_PROGRESS")
        
        total_assets = 0
        audited_assets = 0
        
        for session in all_sessions:
            total_assets += session.total_assets or 0
            audited_assets += session.audited_assets or 0
        
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
    def get_audit_by_id(
        audit_id: str,
        db: Session,
        current_user: Union[User, dict]
    ):
        current_user = AuditService._ensure_user_object(current_user)
        
        query = db.query(AuditPlan).filter(
            AuditPlan.id == audit_id,
            AuditPlan.is_active == True
        )

        if current_user.role == "ADMIN":
            pass
        elif current_user.role == "CLIENT_ADMIN":
            query = query.filter(AuditPlan.client_id == current_user.client_id)
        else:
            query = query.filter(AuditPlan.auditor_id == current_user.id)

        audit = query.first()
        if not audit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit not found"
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
            auditor_id=audit.auditor_id,
            auditor_name=audit.auditor.full_name if audit.auditor else "",
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
        current_user: Union[User, dict]
    ) -> AuditPlanResponse:
        current_user = AuditService._ensure_user_object(current_user)
        
        query = db.query(AuditPlan).filter(
            AuditPlan.id == audit_id,
            AuditPlan.is_active == True
        )
        
        if current_user.role == "ADMIN":
            pass
        elif current_user.role == "CLIENT_ADMIN":
            query = query.filter(AuditPlan.client_id == current_user.client_id)
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this audit"
            )
        
        audit = query.first()
        if not audit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit not found"
            )
        
        if payload.name is not None:
            audit.name = payload.name
        if payload.description is not None:
            audit.description = payload.description
        if payload.auditor_id is not None:
            audit.auditor_id = payload.auditor_id
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
        
        audit.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(audit)
        
        return AuditPlanResponse(
            id=audit.id,
            name=audit.name,
            description=audit.description,
            auditor_id=audit.auditor_id,
            auditor_name=audit.auditor.full_name if audit.auditor else "",
            frequency_unit=audit.frequency_unit,
            frequency_interval=audit.frequency_interval,
            start_date=audit.start_date,
            end_date=audit.end_date,
            next_run_date=audit.next_run_date,
            status=audit.status,
            created_at=audit.created_at,
            sessions_count=len(audit.sessions) if audit.sessions else 0
        )

    @staticmethod
    def delete_audit(
        audit_id: str,
        db: Session,
        current_user: Union[User, dict]
    ):
        current_user = AuditService._ensure_user_object(current_user)
        
        query = db.query(AuditPlan).filter(
            AuditPlan.id == audit_id,
            AuditPlan.is_active == True
        )
        
        if current_user.role == "ADMIN":
            pass
        elif current_user.role == "CLIENT_ADMIN":
            query = query.filter(AuditPlan.client_id == current_user.client_id)
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this audit"
            )
        
        audit = query.first()
        if not audit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit not found"
            )
        
        active_sessions = db.query(AuditSession).filter(
            AuditSession.audit_plan_id == audit_id,
            AuditSession.status.in_(["PENDING", "IN_PROGRESS"])
        ).first()
        
        if active_sessions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete audit with active sessions"
            )
        
        audit.is_active = False
        db.commit()
        
        return {"success": True, "message": "Audit deleted successfully"}

    @staticmethod
    def get_audit_session(
        db: Session,
        audit_id: str,
        current_user: Union[User, dict]
    ) -> AuditSession:
        current_user = AuditService._ensure_user_object(current_user)
        
        session = db.query(AuditSession).join(AuditPlan).filter(
            AuditPlan.id == audit_id,
            AuditSession.assigned_to == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit not found or you don't have access"
            )
        return session

    @staticmethod
    def get_audit_assets(
        db: Session,
        audit_id: str
    ) -> Dict[str, Asset]:
        targets = db.query(AuditTarget).filter(
            AuditTarget.audit_plan_id == audit_id
        ).all()
        
        assets_map = {}
        for target in targets:
            assets = []
            if target.target_type == AuditTargetType.ASSET:
                assets = db.query(Asset).filter(
                    Asset.id == target.target_id,
                    Asset.is_active == True
                ).all()
            elif target.target_type == AuditTargetType.LOCATION:
                assets = db.query(Asset).filter(
                    Asset.location_id == target.target_id,
                    Asset.is_active == True
                ).all()
            elif target.target_type == AuditTargetType.DEPARTMENT:
                assets = db.query(Asset).filter(
                    Asset.department_id == target.target_id,
                    Asset.is_active == True
                ).all()
            elif target.target_type == AuditTargetType.CATEGORY:
                assets = db.query(Asset).filter(
                    Asset.category_id == target.target_id,
                    Asset.is_active == True
                ).all()
            
            for asset in assets:
                assets_map[asset.id] = asset
        
        return assets_map

    @staticmethod
    def start_audit_session(
        audit_id: str,
        db: Session,
        current_user: Union[User, dict]
    ):
        current_user = AuditService._ensure_user_object(current_user)
        
        session = db.query(AuditSession).join(AuditPlan).filter(
            AuditPlan.id == audit_id,
            AuditSession.assigned_to == current_user.id,
            AuditSession.status == AuditSessionStatus.PENDING
        ).first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No pending audit session found"
            )

        audit_plan = session.audit_plan
        assets_map = AuditService.get_audit_assets(db, audit_plan.id)
        assets = list(assets_map.values())

        session.total_assets = len(assets)
        session.audited_assets = 0
        session.status = AuditSessionStatus.IN_PROGRESS
        session.started_at = datetime.utcnow()
        session.conducted_by = current_user.id

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
            audit_plan_id=session.audit_plan_id,
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
        current_user: Union[User, dict]
    ):
        return AuditService.start_audit_session(audit_id, db, current_user)

    @staticmethod
    def scan_asset(
        db: Session,
        audit_id: str,
        request: ScanAssetRequest,
        current_user: Union[User, dict]
    ) -> ScanAssetResponse:
        session = AuditService.get_audit_session(db, audit_id, current_user)

        if session.status != AuditSessionStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Audit session is not active"
            )

        asset = db.query(Asset).filter(
            Asset.id == request.asset_id,
            Asset.is_active == True
        ).first()

        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset not found"
            )

        audit_result = db.query(AuditResult).filter(
            AuditResult.audit_session_id == session.id,
            AuditResult.asset_id == asset.id
        ).first()

        if not audit_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset not part of this audit"
            )

        if audit_result.status != AuditResultStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Asset already audited"
            )

        return ScanAssetResponse(
            asset_id=asset.id,
            asset_name=asset.name,
            serial_number=asset.serial_number,
            qr_code_url=asset.qr_code_url,
            location=asset.location.name if asset.location else None,
            expected_condition=asset.asset_condition,
            already_audited=False
        )

    @staticmethod
    def scan_asset_wrapper(
        db: Session,
        audit_id: str,
        asset_id: str,
        current_user: Union[User, dict]
    ) -> ScanAssetResponse:
        request = ScanAssetRequest(asset_id=asset_id)
        return AuditService.scan_asset(db, audit_id, request, current_user)

    @staticmethod
    def get_asset_details(
        db: Session,
        audit_id: str,
        asset_id: str,
        current_user: Union[User, dict]
    ) -> AuditAssetDetailsResponse:
        current_user = AuditService._ensure_user_object(current_user)
        
        session = db.query(AuditSession).join(AuditPlan).filter(
            AuditPlan.id == audit_id,
            AuditSession.assigned_to == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit session not found or you don't have access"
            )
        
        asset = db.query(Asset).filter(
            Asset.id == asset_id,
            Asset.is_active == True
        ).first()
        
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset not found"
            )
        
        audit_result = db.query(AuditResult).filter(
            AuditResult.audit_session_id == session.id,
            AuditResult.asset_id == asset.id
        ).first()
        
        return AuditAssetDetailsResponse(
            asset_id=asset.id,
            asset_name=asset.name,
            asset_code=getattr(asset, "asset_code", None),
            serial_number=asset.serial_number,
            manufacturer=asset.manufacturer,
            model=asset.model,
            category=asset.category.name if asset.category else None,
            department=asset.department.name if asset.department else None,
            expected_location=asset.location.name if asset.location else None,
            expected_latitude=asset.current_latitude,
            expected_longitude=asset.current_longitude,
            asset_condition=asset.asset_condition,
            audit_status=audit_result.status if audit_result else "PENDING",
            condition_status=audit_result.condition_status if audit_result else None,
            quantity_expected=1,
            quantity_found=audit_result.quantity_found if audit_result else 0,
            remarks=audit_result.remarks if audit_result else None,
            audit_image_url=audit_result.photo_url if audit_result else None,
            already_audited=audit_result.status != "PENDING" if audit_result else False
        )

    @staticmethod
    def submit_asset_audit(
        db: Session,
        audit_id: str,
        asset_id: str,
        audit_status: str,
        condition_status: str,
        quantity_found: int,
        remarks: Optional[str],
        audit_latitude: float,
        audit_longitude: float,
        photo: Optional[UploadFile],
        current_user: Union[User, dict]
    ):
        session = AuditService.get_audit_session(db, audit_id, current_user)

        if session.status != AuditSessionStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Audit session is not active"
            )

        asset = db.query(Asset).filter(
            Asset.id == asset_id,
            Asset.is_active == True
        ).first()

        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset not found"
            )

        audit_result = db.query(AuditResult).filter(
            AuditResult.audit_session_id == session.id,
            AuditResult.asset_id == asset.id
        ).first()

        if not audit_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset not part of this audit"
            )

        current_user = AuditService._ensure_user_object(current_user)
        
        is_new = audit_result.status == AuditResultStatus.PENDING
        
        audit_result.status = audit_status
        audit_result.condition_status = condition_status
        audit_result.quantity_found = quantity_found
        audit_result.remarks = remarks
        audit_result.audit_latitude = audit_latitude
        audit_result.audit_longitude = audit_longitude
        
        if photo:
            try:
                ext = photo.filename.split('.')[-1] if photo.filename else 'jpg'
                filename = f"audit_{audit_id}_{asset_id}_{uuid.uuid4().hex[:8]}.{ext}"
                upload_result = cloudinary.uploader.upload(
                    photo.file,
                    folder=f"assetiq/{asset.client_id}/audits/{audit_id}",
                    public_id=filename,
                    overwrite=True
                )
                audit_result.photo_url = upload_result.get('secure_url')
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to upload photo: {str(e)}"
                )

        audit_result.audited_by = current_user.id
        audit_result.audited_at = datetime.utcnow()

        if is_new:
            session.audited_assets += 1

        db.commit()
        db.refresh(audit_result)

        remaining = session.total_assets - session.audited_assets
        completion = round((session.audited_assets / session.total_assets) * 100, 2) if session.total_assets > 0 else 0

        return SubmitAssetAuditResponse(
            message="Asset audited successfully" if is_new else "Asset audit updated",
            audit_id=session.audit_plan_id,
            session_id=session.id,
            asset_id=asset.id,
            asset_name=asset.name,
            audited_assets=session.audited_assets,
            total_assets=session.total_assets,
            remaining_assets=remaining,
            completion_percentage=completion,
            is_complete=session.audited_assets >= session.total_assets
        )

    @staticmethod
    def complete_audit_session(
        db: Session,
        audit_id: str,
        current_user: Union[User, dict]
    ):
        session = AuditService.get_audit_session(db, audit_id, current_user)

        if session.status != AuditSessionStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Audit session is not active. Status: {session.status}"
            )

        pending = db.query(AuditResult).filter(
            AuditResult.audit_session_id == session.id,
            AuditResult.status == AuditResultStatus.PENDING
        ).count()

        if pending > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot complete audit. {pending} asset(s) are still pending"
            )

        session.status = AuditSessionStatus.COMPLETED
        session.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(session)

        return {
            "success": True,
            "message": "Audit completed successfully",
            "audit_id": session.audit_plan_id,
            "session_id": session.id,
            "status": session.status,
            "completed_at": session.completed_at
        }

    @staticmethod
    def complete_audit_session_manual(
        db: Session,
        audit_id: str,
        current_user: Union[User, dict]
    ):
        return AuditService.complete_audit_session(db, audit_id, current_user)

    @staticmethod
    def get_audit_summary(
        db: Session,
        audit_id: str,
        current_user: Union[User, dict]
    ) -> AuditSummaryResponse:
        session = AuditService.get_audit_session(db, audit_id, current_user)
        
        results = db.query(AuditResult).filter(
            AuditResult.audit_session_id == session.id
        ).all()

        in_place = sum(1 for r in results if r.status == AuditResultStatus.IN_PLACE)
        dislocated = sum(1 for r in results if r.status == AuditResultStatus.DISLOCATED)
        not_found = sum(1 for r in results if r.status == AuditResultStatus.NOT_FOUND)
        lost = sum(1 for r in results if r.status == AuditResultStatus.LOST)

        total = session.total_assets
        audited = session.audited_assets
        remaining = total - audited
        completion = round((audited / total) * 100, 2) if total > 0 else 0

        return AuditSummaryResponse(
            audit_id=session.audit_plan_id,
            session_id=session.id,
            audit_name=session.audit_plan.name,
            status=session.status,
            total_assets=total,
            audited_assets=audited,
            remaining_assets=remaining,
            completion_percentage=completion,
            in_place=in_place,
            dislocated=dislocated,
            not_found=not_found,
            lost=lost
        )

    @staticmethod
    def get_audit_review(
        db: Session,
        audit_id: str,
        current_user: Union[User, dict]
    ) -> AuditReviewResponse:
        """
        Get audit review data for the final review screen.
        
        This endpoint is read-only and becomes the final review screen before 
        the auditor marks remaining assets as LOST or NOT_FOUND and completes the audit.
        """
        # Ensure we have a User object
        current_user = AuditService._ensure_user_object(current_user)
        
        # Get the active audit session
        session = db.query(AuditSession).join(AuditPlan).filter(
            AuditPlan.id == audit_id,
            AuditSession.assigned_to == current_user.id,
            AuditSession.status.in_([AuditSessionStatus.IN_PROGRESS, AuditSessionStatus.PENDING])
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active audit session not found or you don't have access"
            )
        
        # Fetch all AuditResult records for the session with their related assets
        results = db.query(AuditResult).filter(
            AuditResult.audit_session_id == session.id
        ).all()
        
        # Build the asset list
        assets = []
        completed = 0
        pending = 0
        
        for result in results:
            asset = result.asset
            
            # Get department and location names
            department_name = asset.department.name if asset.department else None
            location_name = asset.location.name if asset.location else None
            
            # Count statuses
            if result.status == AuditResultStatus.PENDING:
                pending += 1
            else:
                completed += 1
            
            # Build asset review item
            assets.append(
                AuditReviewAsset(
                    asset_id=str(asset.id),
                    asset_code=getattr(asset, "asset_code", None),
                    asset_name=asset.name,
                    department=department_name,
                    location=location_name,
                    status=result.status,
                    remarks=result.remarks
                )
            )
        
        # Return the review response
        return AuditReviewResponse(
            audit_id=session.audit_plan_id,
            session_id=session.id,
            total_assets=session.total_assets,
            completed_assets=completed,
            pending_assets=pending,
            assets=assets
        )

    @staticmethod
    def get_my_audits(
        db: Session,
        current_user: Union[User, dict]
    ):
        current_user = AuditService._ensure_user_object(current_user)
        
        sessions = db.query(AuditSession).join(AuditPlan).filter(
            AuditSession.assigned_to == current_user.id
        ).order_by(AuditSession.scheduled_date.asc()).all()

        response = []
        for session in sessions:
            completion = round((session.audited_assets / session.total_assets) * 100, 2) if session.total_assets > 0 else 0
            response.append(
                MyAuditResponse(
                    audit_id=session.audit_plan_id,
                    session_id=session.id,
                    audit_name=session.audit_plan.name,
                    status=session.status,
                    start_date=session.audit_plan.start_date,
                    end_date=session.audit_plan.end_date,
                    scheduled_date=session.scheduled_date,
                    total_assets=session.total_assets,
                    audited_assets=session.audited_assets,
                    completion_percentage=completion
                )
            )
        return response

    @staticmethod
    def get_my_audits_simple(
        db: Session,
        current_user: Union[User, dict]
    ):
        return AuditService.get_my_audits(db, current_user)

    @staticmethod
    def get_audit_details(
        db: Session,
        audit_id: str,
        current_user: Union[User, dict]
    ) -> AuditDetailsResponse:
        session = AuditService.get_audit_session(db, audit_id, current_user)
        assets_map = AuditService.get_audit_assets(db, audit_id)

        audited_ids = {
            r.asset_id for r in db.query(AuditResult.asset_id).filter(
                AuditResult.audit_session_id == session.id,
                AuditResult.status != AuditResultStatus.PENDING
            ).all()
        }

        asset_list = []
        for asset in assets_map.values():
            asset_list.append(
                AuditAssetResponse(
                    asset_id=asset.id,
                    asset_name=asset.name,
                    serial_number=asset.serial_number,
                    qr_code_url=asset.qr_code_url,
                    location=asset.location.name if asset.location else None,
                    audit_status="AUDITED" if asset.id in audited_ids else "PENDING"
                )
            )

        completion = round((session.audited_assets / session.total_assets) * 100, 2) if session.total_assets > 0 else 0

        return AuditDetailsResponse(
            audit_id=session.audit_plan_id,
            session_id=session.id,
            audit_name=session.audit_plan.name,
            description=session.audit_plan.description,
            status=session.status,
            scheduled_date=session.scheduled_date,
            start_date=session.audit_plan.start_date,
            end_date=session.audit_plan.end_date,
            total_assets=session.total_assets,
            audited_assets=session.audited_assets,
            completion_percentage=completion,
            assets=asset_list
        )

    @staticmethod
    def get_audit_report(
        db: Session,
        audit_id: str,
        current_user: Union[User, dict]
    ) -> AuditReportResponse:
        current_user = AuditService._ensure_user_object(current_user)
        
        audit = db.query(AuditPlan).filter(
            AuditPlan.id == audit_id,
            AuditPlan.is_active == True
        ).first()

        if not audit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit not found"
            )

        session = db.query(AuditSession).filter(
            AuditSession.audit_plan_id == audit.id
        ).order_by(AuditSession.created_at.desc()).first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit session not found"
            )

        results = db.query(AuditResult).filter(
            AuditResult.audit_session_id == session.id
        ).all()

        total = len(results)
        audited = sum(1 for r in results if r.status != AuditResultStatus.PENDING)
        pending = total - audited
        verified = sum(1 for r in results if r.status == AuditResultStatus.IN_PLACE)
        dislocated = sum(1 for r in results if r.status == AuditResultStatus.DISLOCATED)
        lost = sum(1 for r in results if r.status == AuditResultStatus.LOST)
        not_found = sum(1 for r in results if r.status == AuditResultStatus.NOT_FOUND)

        completion = round((audited / total) * 100, 2) if total > 0 else 0
        verification = round((verified / total) * 100, 2) if total > 0 else 0

        target_name = None
        audit_type = None
        if audit.targets:
            target = audit.targets[0]
            audit_type = target.target_type
            if target.target_type == AuditTargetType.LOCATION:
                target_name = db.query(Location.name).filter(Location.id == target.target_id).scalar()
            elif target.target_type == AuditTargetType.DEPARTMENT:
                target_name = db.query(Department.name).filter(Department.id == target.target_id).scalar()

        duration = None
        if session.started_at and session.completed_at:
            diff = session.completed_at - session.started_at
            hours = int(diff.total_seconds() // 3600)
            minutes = int((diff.total_seconds() % 3600) // 60)
            duration = f"{hours}h {minutes}m"

        details = []
        for result in results:
            asset = result.asset
            details.append(
                AssetVerificationDetail(
                    asset_id=str(asset.id),
                    asset_code=getattr(asset, "asset_code", "") or "",
                    asset_name=asset.name,
                    serial_number=asset.serial_number,
                    manufacturer=asset.manufacturer,
                    model=asset.model,
                    category=asset.category.name if asset.category else None,
                    department=asset.department.name if asset.department else None,
                    expected_location=result.expected_location.name if result.expected_location else None,
                    audited_location=asset.location.name if asset.location else None,
                    audit_status=result.status,
                    condition_status=result.condition_status,
                    quantity_found=result.quantity_found,
                    location_status=result.location_status,
                    audited_by=result.auditor.full_name if result.auditor else None,
                    audited_at=result.audited_at,
                    remarks=result.remarks,
                    audit_image_url=result.photo_url,
                    expected_latitude=result.expected_latitude,
                    expected_longitude=result.expected_longitude,
                    audit_latitude=result.audit_latitude,
                    audit_longitude=result.audit_longitude
                )
            )

        return AuditReportResponse(
            report_information=AuditReportInformation(
                report_id=str(uuid.uuid4()),
                generated_at=datetime.utcnow(),
                generated_by=current_user.full_name
            ),
            audit_information=AuditInformation(
                audit_id=str(audit.id),
                audit_code=f"AUD-{str(audit.id)[:8].upper()}",
                audit_name=audit.name,
                audit_status=session.status,
                audit_type=audit_type,
                target_name=target_name,
                scheduled_date=session.scheduled_date,
                started_at=session.started_at,
                completed_at=session.completed_at,
                audit_duration=duration
            ),
            audit_summary=AuditSummary(
                total_assets=total,
                audited_assets=audited,
                pending_assets=pending,
                verified_assets=verified,
                dislocated_assets=dislocated,
                lost_assets=lost,
                not_found_assets=not_found,
                completion_percentage=completion,
                verification_percentage=verification
            ),
            asset_verification_details=details
        )