from pydantic import BaseModel
from datetime import datetime


class TransferCreate(BaseModel):
    asset_id: str
    to_user_id: str
    notes: str | None = None
    requires_approval: bool = False
    due_by: datetime | None = None


class TransferResponse(BaseModel):
    id: str
    asset_id: str
    from_user_id: str | None
    to_user_id: str | None
    status: str
    dispatched_by: str
    notes: str | None
    requires_approval: bool
    approved_by: str | None
    dispatched_at: datetime
    received_at: datetime | None

    class Config:
        from_attributes = True