import uuid
from typing import Optional

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from sqlalchemy import func

from app.models.clients import Client
from app.models.office_timing import OfficeTiming
from app.models.attendance import Attendance
from app.models.users import User

from app.schemas.office_timing import (
    OfficeTimingCreate,
    OfficeTimingUpdate,
    OfficeTimingResponse,
    OfficeTimingListResponse,
)


class OfficeTimingService:
    
    @staticmethod
    def create_office_timing(
        payload: OfficeTimingCreate,
        db: Session,
        current_user: dict,
    ) -> OfficeTimingResponse:
        """
        Create a new office timing configuration with geofencing data.
        """
        # Permission Check
        role = current_user.get("role")
        
        if role == "PLATFORM_ADMIN":
            if not payload.client_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="client_id is required."
                )
            client_id = payload.client_id
            
        elif role == "CLIENT_ADMIN":
            client_id = current_user.get("client_id")
            
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to create office timings."
            )
        
        # Validate Client
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
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found."
            )
        
        # Check for duplicate name within client
        existing = (
            db.query(OfficeTiming)
            .filter(
                OfficeTiming.client_id == client_id,
                OfficeTiming.name == payload.name,
                OfficeTiming.is_active == True,
            )
            .first()
        )
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Office timing with name '{payload.name}' already exists for this client."
            )
        
        # Validate Time
        if payload.check_out_time <= payload.check_in_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Check-out time must be greater than check-in time."
            )
        
        # Create OfficeTiming with geofencing data
        office_timing = OfficeTiming(
            id=str(uuid.uuid4()),
            client_id=client_id,
            name=payload.name,
            check_in_time=payload.check_in_time,
            check_out_time=payload.check_out_time,
            late_after_minutes=payload.late_after_minutes,
            half_day_after_minutes=payload.half_day_after_minutes,
            latitude=payload.latitude,
            longitude=payload.longitude,
            radius_in_meters=payload.radius_in_meters,
            is_active=True
        )
        
        # Save
        db.add(office_timing)
        db.commit()
        db.refresh(office_timing)
        
        # Return Response
        return OfficeTimingResponse(
            id=office_timing.id,
            client_id=office_timing.client_id,
            name=office_timing.name,
            check_in_time=office_timing.check_in_time,
            check_out_time=office_timing.check_out_time,
            late_after_minutes=office_timing.late_after_minutes,
            half_day_after_minutes=office_timing.half_day_after_minutes,
            latitude=office_timing.latitude,
            longitude=office_timing.longitude,
            radius_in_meters=office_timing.radius_in_meters,
            is_active=office_timing.is_active,
            created_at=office_timing.created_at,
            updated_at=office_timing.updated_at,
        )
    
    @staticmethod
    def get_office_timings(
        db: Session,
        current_user: dict,
        page: int = 1,
        size: int = 10,
    ) -> OfficeTimingListResponse:
        """
        Get paginated list of office timings with permission filtering.
        """
        role = current_user.get("role")
        
        # Build base query
        query = db.query(OfficeTiming).filter(OfficeTiming.is_active == True)
        
        # Apply role-based filtering
        if role == "CLIENT_ADMIN":
            query = query.filter(
                OfficeTiming.client_id == current_user.get("client_id")
            )
        elif role == "PLATFORM_ADMIN":
            # Platform admin can see all
            pass
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view office timings."
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        records = (
            query
            .order_by(OfficeTiming.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )
        
        # Return response
        return OfficeTimingListResponse(
            items=[
                OfficeTimingResponse(
                    id=item.id,
                    client_id=item.client_id,
                    name=item.name,
                    check_in_time=item.check_in_time,
                    check_out_time=item.check_out_time,
                    late_after_minutes=item.late_after_minutes,
                    half_day_after_minutes=item.half_day_after_minutes,
                    latitude=item.latitude,
                    longitude=item.longitude,
                    radius_in_meters=item.radius_in_meters,
                    is_active=item.is_active,
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                )
                for item in records
            ],
            total=total,
            page=page,
            size=size,
        )
    
    @staticmethod
    def get_office_timing(
        office_timing_id: str,
        db: Session,
        current_user: dict,
    ) -> OfficeTimingResponse:
        """
        Get a single office timing by ID with permission check.
        """
        office_timing = (
            db.query(OfficeTiming)
            .filter(
                OfficeTiming.id == office_timing_id,
                OfficeTiming.is_active == True,
            )
            .first()
        )
        
        if not office_timing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Office timing not found."
            )
        
        # Permission check
        role = current_user.get("role")
        
        if role == "CLIENT_ADMIN":
            if office_timing.client_id != current_user.get("client_id"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view this office timing."
                )
        elif role != "PLATFORM_ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this office timing."
            )
        
        return OfficeTimingResponse(
            id=office_timing.id,
            client_id=office_timing.client_id,
            name=office_timing.name,
            check_in_time=office_timing.check_in_time,
            check_out_time=office_timing.check_out_time,
            late_after_minutes=office_timing.late_after_minutes,
            half_day_after_minutes=office_timing.half_day_after_minutes,
            latitude=office_timing.latitude,
            longitude=office_timing.longitude,
            radius_in_meters=office_timing.radius_in_meters,
            is_active=office_timing.is_active,
            created_at=office_timing.created_at,
            updated_at=office_timing.updated_at,
        )
    
    @staticmethod
    def update_office_timing(
        office_timing_id: str,
        payload: OfficeTimingUpdate,
        db: Session,
        current_user: dict,
    ) -> OfficeTimingResponse:
        """
        Update an existing office timing configuration.
        """
        # Fetch office timing
        office_timing = (
            db.query(OfficeTiming)
            .filter(
                OfficeTiming.id == office_timing_id,
                OfficeTiming.is_active == True,
            )
            .first()
        )
        
        if not office_timing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Office timing not found."
            )
        
        # Permission check
        role = current_user.get("role")
        
        if role == "CLIENT_ADMIN":
            if office_timing.client_id != current_user.get("client_id"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to update this office timing."
                )
        elif role != "PLATFORM_ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this office timing."
            )
        
        # Validate time if either time is being updated
        check_in = payload.check_in_time or office_timing.check_in_time
        check_out = payload.check_out_time or office_timing.check_out_time
        
        if check_out <= check_in:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Check-out time must be greater than check-in time."
            )
        
        # Update fields
        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(office_timing, key, value)
        
        # Save
        db.commit()
        db.refresh(office_timing)
        
        # Return response
        return OfficeTimingResponse(
            id=office_timing.id,
            client_id=office_timing.client_id,
            name=office_timing.name,
            check_in_time=office_timing.check_in_time,
            check_out_time=office_timing.check_out_time,
            late_after_minutes=office_timing.late_after_minutes,
            half_day_after_minutes=office_timing.half_day_after_minutes,
            latitude=office_timing.latitude,
            longitude=office_timing.longitude,
            radius_in_meters=office_timing.radius_in_meters,
            is_active=office_timing.is_active,
            created_at=office_timing.created_at,
            updated_at=office_timing.updated_at,
        )
    
    @staticmethod
    def delete_office_timing(
        office_timing_id: str,
        db: Session,
        current_user: dict,
    ) -> dict:
        """
        Soft delete an office timing configuration.
        """
        # Fetch office timing
        office_timing = (
            db.query(OfficeTiming)
            .filter(
                OfficeTiming.id == office_timing_id,
                OfficeTiming.is_active == True,
            )
            .first()
        )
        
        if not office_timing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Office timing not found."
            )
        
        # Permission check
        role = current_user.get("role")
        
        if role != "CLIENT_ADMIN" or role != "PLATFORM_ADMIN" :
            if office_timing.client_id != current_user.get("client_id"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to delete this office timing."
                )
        
        # Check if there are users assigned to this timing
        user_count = (
            db.query(func.count(User.id))
            .filter(
                User.office_timing_id == office_timing_id,
                User.is_active == True
            )
            .scalar()
        )
        
        if user_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete office timing. {user_count} active users are assigned to it."
            )
        
        # Check if there are attendance records using this timing
        attendance_count = (
            db.query(func.count(Attendance.id))
            .filter(Attendance.office_timing_id == office_timing_id)
            .scalar()
        )
        
        if attendance_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete office timing. It has {attendance_count} attendance records."
            )
        
        # Soft delete
        office_timing.is_active = False
        db.commit()
        
        return {
            "message": "Office timing deleted successfully.",
            "id": office_timing_id
        }