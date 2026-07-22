# app/schemas/tracking.py

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field


# ==========================================================
# Assets Available for Tracking
# ==========================================================

class TrackingAssetResponse(BaseModel):
    asset_id: str
    asset_name: str
    serial_number: Optional[str] = None
    asset_tag: Optional[str] = None


# ==========================================================
# Start Tracking
# ==========================================================

class StartTrackingRequest(BaseModel):
    asset_ids: List[str] = Field(
        ...,
        min_length=1,
        description="List of asset IDs to track"
    )


class StartTrackingResponse(BaseModel):
    tracking_session_id: str
    status: str = "ACTIVE"
    started_at: datetime
    message: str


# ==========================================================
# GPS Update
# ==========================================================

class TrackingUpdateRequest(BaseModel):
    tracking_session_id: str = Field(..., description="ID of the tracking session")
    asset_id: str = Field(..., description="ID of the asset being tracked")

    latitude: Decimal = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: Decimal = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")

    accuracy: Optional[Decimal] = Field(None, ge=0, description="Accuracy in meters")
    altitude: Optional[Decimal] = Field(None, description="Altitude in meters")
    speed: Optional[Decimal] = Field(None, ge=0, description="Speed in km/h")
    heading: Optional[Decimal] = Field(None, ge=0, le=360, description="Heading in degrees")

    recorded_at: datetime = Field(..., description="Timestamp when GPS data was recorded")


class TrackingUpdateResponse(BaseModel):
    message: str = "GPS data recorded successfully"
    tracking_session_id: str
    asset_id: str
    recorded_at: datetime


# ==========================================================
# Stop Tracking
# ==========================================================

class StopTrackingRequest(BaseModel):
    tracking_session_id: str = Field(..., description="ID of the tracking session to stop")


class StopTrackingResponse(BaseModel):
    message: str
    tracking_session_id: str
    ended_at: datetime


# ==========================================================
# Session Details (Single API for Live + Path)
# ==========================================================

class TrackingPathPoint(BaseModel):
    latitude: Decimal
    longitude: Decimal
    recorded_at: datetime


class TrackingAssetDetails(BaseModel):
    asset_id: str
    asset_name: str
    serial_number: Optional[str] = None
    asset_tag: Optional[str] = None

    current_latitude: Optional[Decimal] = None
    current_longitude: Optional[Decimal] = None
    last_updated: Optional[datetime] = None

    path: List[TrackingPathPoint] = Field(default_factory=list, description="Full path history for this asset")


class TrackingSessionResponse(BaseModel):
    tracking_session_id: str
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None

    tracked_by_user_id: str
    tracked_by_name: str

    assets: List[TrackingAssetDetails] = Field(default_factory=list)


# ==========================================================
# Session List
# ==========================================================

class TrackingSessionListItem(BaseModel):
    tracking_session_id: str
    tracked_by_user_id: str
    tracked_by_name: str
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    tracked_assets: int


class TrackingSessionListResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[TrackingSessionListItem]


# ==========================================================
# Session Filters
# ==========================================================

class TrackingSessionFilters(BaseModel):
    client_id: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(ACTIVE|STOPPED)$")
    started_by_user_id: Optional[str] = None
    started_after: Optional[datetime] = None
    started_before: Optional[datetime] = None
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)