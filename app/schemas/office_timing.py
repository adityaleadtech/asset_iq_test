# app/schemas/office_timing.py

from datetime import datetime, time
from typing import Optional

from pydantic import BaseModel, ConfigDict


class OfficeTimingCreate(BaseModel):
    """Schema for creating a new office timing configuration."""
    client_id: Optional[str] = None
    location_id: str
    name: str
    check_in_time: time
    check_out_time: time
    late_after_minutes: int = 15
    half_day_after_minutes: int = 240


class OfficeTimingUpdate(BaseModel):
    """Schema for updating an existing office timing configuration."""
    location_id: Optional[str] = None
    name: Optional[str] = None
    check_in_time: Optional[time] = None
    check_out_time: Optional[time] = None
    late_after_minutes: Optional[int] = None
    half_day_after_minutes: Optional[int] = None
    is_active: Optional[bool] = None


class OfficeTimingResponse(BaseModel):
    """Schema for office timing response (single item)."""
    id: str
    client_id: str
    location_id: str
    location_name: str

    name: str

    check_in_time: time
    check_out_time: time

    late_after_minutes: int
    half_day_after_minutes: int

    is_active: bool

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OfficeTimingListResponse(BaseModel):
    """Schema for paginated office timing list response."""
    items: list[OfficeTimingResponse]
    total: int
    page: int
    size: int