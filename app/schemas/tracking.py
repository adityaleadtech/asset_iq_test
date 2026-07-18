from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


# ==========================================
# Asset List
# ==========================================

class TrackingAssetResponse(BaseModel):
    id: str
    name: str
    serial_number: str | None = None
    model: str | None = None
    manufacturer: str | None = None
    is_tracking: bool

    class Config:
        from_attributes = True


# ==========================================
# Start Tracking
# ==========================================

class StartTrackingRequest(BaseModel):
    asset_ids: list[str] = Field(
        min_length=1,
        description="List of asset IDs to track"
    )


class StartTrackingResponse(BaseModel):
    tracking_session_id: str
    tracked_assets: int
    started_at: datetime
    message: str


# ==========================================
# GPS Update
# ==========================================

class TrackingUpdateRequest(BaseModel):
    tracking_session_id: str

    latitude: Decimal
    longitude: Decimal

    accuracy: Decimal | None = None
    speed: Decimal | None = None

    recorded_at: datetime


# ==========================================
# Stop Tracking
# ==========================================

class StopTrackingRequest(BaseModel):
    tracking_session_id: str


class StopTrackingResponse(BaseModel):
    message: str
    ended_at: datetime


# ==========================================
# Live Location
# ==========================================

class LiveTrackingResponse(BaseModel):
    asset_id: str
    asset_name: str

    latitude: Decimal | None
    longitude: Decimal | None

    last_updated: datetime | None

    is_tracking: bool

    class Config:
        from_attributes = True



from datetime import datetime
from decimal import Decimal


class LiveTrackingAssetResponse(BaseModel):
    tracking_session_id: str

    asset_id: str
    asset_name: str

    latitude: Decimal | None
    longitude: Decimal | None

    last_updated: datetime | None

    tracked_by_user_id: str
    tracked_by_name: str

    class Config:
        from_attributes = True


from datetime import datetime
from pydantic import BaseModel


class TrackingSessionAssetResponse(BaseModel):
    asset_id: str
    asset_name: str
    serial_number: str | None = None
    manufacturer: str | None = None
    model: str | None = None

    class Config:
        from_attributes = True


class TrackingSessionDetailsResponse(BaseModel):
    tracking_session_id: str

    status: str

    started_at: datetime

    ended_at: datetime | None = None

    tracked_by_user_id: str

    tracked_by_name: str

    assets: list[TrackingSessionAssetResponse]


from datetime import datetime
from pydantic import BaseModel


class TrackingSessionListItem(BaseModel):
    tracking_session_id: str

    tracked_by_user_id: str
    tracked_by_name: str

    status: str

    started_at: datetime
    ended_at: datetime | None = None

    tracked_assets: int


class TrackingSessionListResponse(BaseModel):
    total: int

    page: int

    size: int

    items: list[TrackingSessionListItem]




from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class TrackingHistoryPoint(BaseModel):
    latitude: Decimal

    longitude: Decimal

    accuracy: Decimal | None = None

    speed: Decimal | None = None

    recorded_at: datetime

    tracking_session_id: str


class TrackingHistoryResponse(BaseModel):
    asset_id: str

    asset_name: str

    total_points: int

    history: list[TrackingHistoryPoint]