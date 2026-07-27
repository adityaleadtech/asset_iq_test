# app/schemas/office_timing.py

from datetime import datetime, time
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
import re


class OfficeTimingBase(BaseModel):
    """Base schema for office timing with common fields."""
    name: str = Field(..., min_length=1, max_length=100)
    check_in_time: time
    check_out_time: time
    late_after_minutes: int = Field(default=15, ge=0, le=1440)
    half_day_after_minutes: int = Field(default=240, ge=0, le=1440)
    
    # Geofencing fields (NEW - replaces location_id)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius_in_meters: int = Field(default=100, ge=10, le=5000)
    
    is_active: bool = True

    @field_validator('check_out_time')
    def validate_check_out_after_check_in(cls, v, info):
        if 'check_in_time' in info.data:
            check_in = info.data['check_in_time']
            if v <= check_in:
                raise ValueError('Check-out time must be after check-in time')
        return v

    @field_validator('radius_in_meters')
    def validate_radius(cls, v):
        if v < 10:
            raise ValueError('Radius must be at least 10 meters')
        if v > 5000:
            raise ValueError('Radius cannot exceed 5000 meters (5km)')
        return v


class OfficeTimingCreate(BaseModel):
    """Schema for creating a new office timing configuration."""
    client_id: Optional[str] = None
    # ❌ REMOVED: location_id
    name: str = Field(..., min_length=1, max_length=100)
    check_in_time: time
    check_out_time: time
    late_after_minutes: int = Field(default=15, ge=0, le=1440)
    half_day_after_minutes: int = Field(default=240, ge=0, le=1440)
    
    # ✅ NEW: Geofencing fields
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius_in_meters: int = Field(default=100, ge=10, le=5000)

    @field_validator('client_id')
    def validate_client_id(cls, v):
        if v is not None and not re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', v, re.I):
            raise ValueError('Invalid client ID format')
        return v

    @field_validator('check_out_time')
    def validate_check_out_after_check_in(cls, v, info):
        if 'check_in_time' in info.data:
            check_in = info.data['check_in_time']
            if v <= check_in:
                raise ValueError('Check-out time must be after check-in time')
        return v

    @field_validator('radius_in_meters')
    def validate_radius(cls, v):
        if v < 10:
            raise ValueError('Radius must be at least 10 meters')
        if v > 5000:
            raise ValueError('Radius cannot exceed 5000 meters (5km)')
        return v


class OfficeTimingUpdate(BaseModel):
    """Schema for updating an existing office timing configuration."""
    # ❌ REMOVED: location_id
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    check_in_time: Optional[time] = None
    check_out_time: Optional[time] = None
    late_after_minutes: Optional[int] = Field(None, ge=0, le=1440)
    half_day_after_minutes: Optional[int] = Field(None, ge=0, le=1440)
    
    # ✅ NEW: Geofencing fields (all optional for updates)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    radius_in_meters: Optional[int] = Field(None, ge=10, le=5000)
    
    is_active: Optional[bool] = None

    @field_validator('check_out_time')
    def validate_check_out_after_check_in(cls, v, info):
        if v is not None and 'check_in_time' in info.data:
            check_in = info.data['check_in_time']
            if check_in is not None and v <= check_in:
                raise ValueError('Check-out time must be after check-in time')
        return v


class OfficeTimingResponse(BaseModel):
    """Schema for office timing response (single item)."""
    id: str
    client_id: str
    # ❌ REMOVED: location_id
    # ❌ REMOVED: location_name
    
    name: str
    
    check_in_time: time
    check_out_time: time
    
    late_after_minutes: int
    half_day_after_minutes: int
    
    # ✅ NEW: Geofencing fields
    latitude: float
    longitude: float
    radius_in_meters: int
    
    is_active: bool
    
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # ✅ NEW: Optional statistics
    total_users_assigned: Optional[int] = 0
    total_attendance_records: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)


class OfficeTimingListResponse(BaseModel):
    """Schema for paginated office timing list response."""
    items: list[OfficeTimingResponse]
    total: int
    page: int
    size: int


class OfficeTimingDetailResponse(OfficeTimingResponse):
    """Detailed office timing response with additional info."""
    # ✅ NEW: Additional fields for detail view
    check_in_time_str: str  # Formatted string for display
    check_out_time_str: str  # Formatted string for display
    timezone: Optional[str] = "UTC"
    
    @field_validator('check_in_time_str', mode='before')
    def format_check_in_time(cls, v, info):
        if 'check_in_time' in info.data:
            return info.data['check_in_time'].strftime('%I:%M %p')
        return v
    
    @field_validator('check_out_time_str', mode='before')
    def format_check_out_time(cls, v, info):
        if 'check_out_time' in info.data:
            return info.data['check_out_time'].strftime('%I:%M %p')
        return v


class OfficeTimingAssignUser(BaseModel):
    """Schema for assigning users to an office timing."""
    user_ids: list[str] = Field(..., min_length=1)
    
    @field_validator('user_ids')
    def validate_user_ids(cls, v):
        for user_id in v:
            if not re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', user_id, re.I):
                raise ValueError(f'Invalid user ID format: {user_id}')
        return v


class OfficeTimingUnassignUser(BaseModel):
    """Schema for unassigning users from an office timing."""
    user_ids: list[str] = Field(..., min_length=1)


class OfficeTimingBulkCreate(BaseModel):
    """Schema for bulk creating office timings."""
    office_timings: list[OfficeTimingCreate]
    
    @field_validator('office_timings')
    def validate_office_timings(cls, v):
        if len(v) > 10:
            raise ValueError('Cannot create more than 10 office timings at once')
        return v


class OfficeTimingBulkResponse(BaseModel):
    """Response for bulk office timing operations."""
    created: list[OfficeTimingResponse]
    failed: list[dict]  # List of {index: int, error: str}
    total_created: int
    total_failed: int