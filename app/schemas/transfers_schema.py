from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from typing import List
from app.enums.transfer_types import TransferType
from typing import List
from datetime import datetime


class TransferAssetCreate(BaseModel):
    asset_id: UUID

    to_department_id: Optional[UUID] = None
    to_location_id: Optional[UUID] = None
    to_user_id: Optional[UUID] = None




class TransferCreate(BaseModel):
    transfer_type: TransferType

    reason: Optional[str] = None
    remarks: Optional[str] = None

    assets: List[TransferAssetCreate]



class TransferResponse(BaseModel):
    id: UUID
    transfer_type: TransferType
    reason: Optional[str]
    remarks: Optional[str]
    transferred_by: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class TransferAssetResponse(BaseModel):
    asset_id: UUID

    from_department_id: Optional[UUID]
    to_department_id: Optional[UUID]

    from_location_id: Optional[UUID]
    to_location_id: Optional[UUID]

    from_user_id: Optional[UUID]
    to_user_id: Optional[UUID]

    class Config:
        from_attributes = True


class TransferDetailResponse(TransferResponse):
    assets: List[TransferAssetResponse]

class TransferAssetDetailResponse(BaseModel):
    asset_id: UUID

    asset_name: str
    asset_tag: str | None = None

    from_department: str | None = None
    to_department: str | None = None

    from_location: str | None = None
    to_location: str | None = None

    from_user: str | None = None
    to_user: str | None = None

    class Config:
        from_attributes = True


class TransferDetailResponse(BaseModel):
    id: UUID

    transfer_type: TransferType

    reason: str | None

    remarks: str | None

    transferred_by: str

    created_at: datetime

    assets: list[TransferAssetDetailResponse]

    class Config:
        from_attributes = True