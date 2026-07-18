from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

class LivePathPoint(BaseModel):
    latitude: Decimal
    longitude: Decimal
    recorded_at: datetime


class LiveTrackingAsset(BaseModel):
    tracking_session_id: str

    asset_id: str
    asset_name: str
    serial_number: str | None = None

    tracked_by_user_id: str
    tracked_by_name: str

    current_latitude: Decimal
    current_longitude: Decimal
    last_updated: datetime

    path: list[LivePathPoint]


class LiveTrackingResponse(BaseModel):
    assets: list[LiveTrackingAsset]