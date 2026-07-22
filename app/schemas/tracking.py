from datetime import datetime
from decimal import Decimal
from typing import Optional

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
    asset_ids: list[str] = Field(
        ...,
        min_length=1
    )


class StartTrackingResponse(BaseModel):
    tracking_session_id: str
    message: str


# ==========================================================
# GPS Update
# ==========================================================

class TrackingUpdateRequest(BaseModel):
    tracking_session_id: str

    latitude: Decimal
    longitude: Decimal

    accuracy: Optional[Decimal] = None
    speed: Optional[Decimal] = None
    recorded_at: datetime = None


# ==========================================================
# Stop Tracking
# ==========================================================

class StopTrackingRequest(BaseModel):
    tracking_session_id: str


class StopTrackingResponse(BaseModel):
    message: str


# ==========================================================
# Session Details
# ==========================================================

class TrackingSessionAssetResponse(BaseModel):
    asset_id: str
    asset_name: str
    serial_number: Optional[str] = None


class TrackingSessionDetailsResponse(BaseModel):
    tracking_session_id: str

    started_at: datetime
    ended_at: Optional[datetime] = None

    tracked_by_user_id: str
    tracked_by_name: str

    assets: list[TrackingSessionAssetResponse]


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
    items: list[TrackingSessionListItem]
# ==========================================================
# Asset History
# ==========================================================

class TrackingHistoryPoint(BaseModel):
    latitude: Decimal
    longitude: Decimal
    recorded_at: datetime


class TrackingHistoryResponse(BaseModel):
    asset_id: str
    asset_name: str

    history: list[TrackingHistoryPoint]


# ==========================================================
# Live Tracking
# ==========================================================

class LivePathPoint(BaseModel):
    latitude: Decimal
    longitude: Decimal
    recorded_at: datetime


class LiveTrackingAsset(BaseModel):
    tracking_session_id: str

    asset_id: str
    asset_name: str
    serial_number: Optional[str] = None

    tracked_by_user_id: str
    tracked_by_name: str

    current_latitude: Optional[Decimal] = None
    current_longitude: Optional[Decimal] = None
    last_updated: Optional[datetime] = None

    path: list[LivePathPoint]


class LiveTrackingResponse(BaseModel):
    assets: list[LiveTrackingAsset]