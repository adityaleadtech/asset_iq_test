# app/services/office_timing_service.py

import uuid

from sqlalchemy.orm import Session

from fastapi import HTTPException, status

from app.models.client import Client
from app.models.location import Location
from app.models.office_timing import OfficeTiming

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
        current_user,
    ):
        """
        Create a new office timing configuration.
        """
        # Permission Check
        role = current_user["role"]
        
        if role == "PLATFORM_ADMIN":
            if not payload.client_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="client_id is required."
                )
            client_id = payload.client_id
            
        elif role == "CLIENT_ADMIN":
            client_id = current_user["client_id"]
            
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
        
        # Validate Location
        location = (
            db.query(Location)
            .filter(
                Location.id == payload.location_id,
                Location.client_id == client_id,
                Location.is_active == True,
            )
            .first()
        )
        
        if not location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Location not found."
            )
        
        # Duplicate Check
        existing = (
            db.query(OfficeTiming)
            .filter(
                OfficeTiming.location_id == payload.location_id,
                OfficeTiming.is_active == True,
            )
            .first()
        )
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Office timing already exists for this location."
            )
        
        # Validate Time
        if payload.check_out_time <= payload.check_in_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Check-out time must be greater than check-in time."
            )
        
        # Create Object
        office_timing = OfficeTiming(
            id=str(uuid.uuid4()),
            client_id=client_id,
            location_id=payload.location_id,
            name=payload.name,
            check_in_time=payload.check_in_time,
            check_out_time=payload.check_out_time,
            late_after_minutes=payload.late_after_minutes,
            half_day_after_minutes=payload.half_day_after_minutes,
        )
        
        # Save
        db.add(office_timing)
        db.commit()
        db.refresh(office_timing)
        
        # Return Response
        return OfficeTimingResponse(
            id=office_timing.id,
            client_id=office_timing.client_id,
            location_id=office_timing.location_id,
            location_name=location.name,
            name=office_timing.name,
            check_in_time=office_timing.check_in_time,
            check_out_time=office_timing.check_out_time,
            late_after_minutes=office_timing.late_after_minutes,
            half_day_after_minutes=office_timing.half_day_after_minutes,
            is_active=office_timing.is_active,
            created_at=office_timing.created_at,
        )
    
    @staticmethod
    def get_office_timings(
        db: Session,
        current_user,
        page: int = 1,
        size: int = 10,
    ):
        """
        Get paginated list of office timings with permission filtering.
        """
        role = current_user["role"]
        
        # Build base query with join to Location
        query = (
            db.query(OfficeTiming)
            .join(Location)
        )
        
        # Apply role-based filtering
        if role == "CLIENT_ADMIN":
            query = query.filter(
                OfficeTiming.client_id == current_user["client_id"]
            )
        elif role != "PLATFORM_ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view office timings."
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        records = (
            query
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
                    location_id=item.location_id,
                    location_name=item.location.name,
                    name=item.name,
                    check_in_time=item.check_in_time,
                    check_out_time=item.check_out_time,
                    late_after_minutes=item.late_after_minutes,
                    half_day_after_minutes=item.half_day_after_minutes,
                    is_active=item.is_active,
                    created_at=item.created_at,
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
        current_user,
    ):
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
        role = current_user["role"]
        
        if role == "CLIENT_ADMIN":
            if office_timing.client_id != current_user["client_id"]:
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
            location_id=office_timing.location_id,
            location_name=office_timing.location.name,
            name=office_timing.name,
            check_in_time=office_timing.check_in_time,
            check_out_time=office_timing.check_out_time,
            late_after_minutes=office_timing.late_after_minutes,
            half_day_after_minutes=office_timing.half_day_after_minutes,
            is_active=office_timing.is_active,
            created_at=office_timing.created_at,
        )
    
    @staticmethod
    def update_office_timing(
        office_timing_id: str,
        payload: OfficeTimingUpdate,
        db: Session,
        current_user,
    ):
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
        role = current_user["role"]
        
        if role == "CLIENT_ADMIN":
            if office_timing.client_id != current_user["client_id"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to update this office timing."
                )
        elif role != "PLATFORM_ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this office timing."
            )
        
        # If location_id is being updated, validate the new location
        if payload.location_id is not None:
            # Verify location exists and belongs to same client
            location = (
                db.query(Location)
                .filter(
                    Location.id == payload.location_id,
                    Location.client_id == office_timing.client_id,
                    Location.is_active == True,
                )
                .first()
            )
            
            if not location:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Location not found or does not belong to this client."
                )
            
            # Check if another active office timing already exists for this location
            existing = (
                db.query(OfficeTiming)
                .filter(
                    OfficeTiming.location_id == payload.location_id,
                    OfficeTiming.is_active == True,
                    OfficeTiming.id != office_timing_id,  # Exclude current record
                )
                .first()
            )
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Office timing already exists for this location."
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
            location_id=office_timing.location_id,
            location_name=office_timing.location.name,
            name=office_timing.name,
            check_in_time=office_timing.check_in_time,
            check_out_time=office_timing.check_out_time,
            late_after_minutes=office_timing.late_after_minutes,
            half_day_after_minutes=office_timing.half_day_after_minutes,
            is_active=office_timing.is_active,
            created_at=office_timing.created_at,
        )
    
    @staticmethod
    def delete_office_timing(
        office_timing_id: str,
        db: Session,
        current_user,
    ):
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
        role = current_user["role"]
        
        if role == "CLIENT_ADMIN":
            if office_timing.client_id != current_user["client_id"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to delete this office timing."
                )
        elif role != "PLATFORM_ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this office timing."
            )
        
        # Soft delete
        office_timing.is_active = False
        db.commit()
        
        return {"message": "Office timing deleted successfully."}