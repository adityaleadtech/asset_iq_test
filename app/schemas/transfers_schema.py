from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List
from datetime import datetime

from app.enums.transfer_types import TransferType


# ============================================================
# 📦 REQUEST SCHEMAS
# ============================================================

class TransferAssetCreate(BaseModel):
    """
    Schema for an asset being transferred.
    """
    asset_id: UUID
    to_department_id: Optional[UUID] = None
    to_location_id: Optional[UUID] = None
    to_user_id: Optional[UUID] = None


class TransferCreate(BaseModel):
    """
    Schema for creating a new transfer.
    """
    transfer_type: TransferType
    reason: Optional[str] = None
    remarks: Optional[str] = None
    assets: List[TransferAssetCreate]


# ============================================================
# 📦 RESPONSE SCHEMAS
# ============================================================

class TransferResponse(BaseModel):
    """
    Schema for transfer response (list view).
    """
    id: UUID
    transfer_type: TransferType
    reason: Optional[str] = None
    remarks: Optional[str] = None
    transferred_by: Optional[str] = None  # Full name of the user
    transferred_by_id: Optional[UUID] = None
    asset_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class TransferAssetResponse(BaseModel):
    """
    Schema for asset details in a transfer (IDs only).
    """
    asset_id: UUID
    from_department_id: Optional[UUID] = None
    to_department_id: Optional[UUID] = None
    from_location_id: Optional[UUID] = None
    to_location_id: Optional[UUID] = None
    from_user_id: Optional[UUID] = None
    to_user_id: Optional[UUID] = None

    class Config:
        from_attributes = True


class TransferAssetDetailResponse(BaseModel):
    """
    Schema for asset details in a transfer (with names).
    """
    asset_id: UUID
    asset_name: str
    asset_code: Optional[str] = None
    serial_number: Optional[str] = None
    
    from_department: Optional[str] = None
    to_department: Optional[str] = None
    
    from_location: Optional[str] = None
    to_location: Optional[str] = None
    
    from_user: Optional[str] = None
    to_user: Optional[str] = None

    class Config:
        from_attributes = True


class TransferDetailResponse(BaseModel):
    """
    Schema for detailed transfer response (single transfer view).
    """
    id: UUID
    transfer_type: TransferType
    reason: Optional[str] = None
    remarks: Optional[str] = None
    transferred_by: Optional[str] = None
    transferred_by_id: Optional[UUID] = None
    created_at: datetime
    assets: List[TransferAssetDetailResponse]

    class Config:
        from_attributes = True


class TransferListResponse(BaseModel):
    """
    Schema for paginated transfer list response.
    """
    items: List[TransferResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================
# 📊 DASHBOARD SCHEMAS
# ============================================================

class RecentTransferResponse(BaseModel):
    """
    Schema for recent transfer in dashboard.
    """
    id: UUID
    transfer_type: TransferType
    reason: Optional[str] = None
    transferred_by: Optional[str] = None
    asset_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class TransferDashboardResponse(BaseModel):
    """
    Schema for transfer dashboard statistics.
    """
    total_transfers: int
    department_transfers: int
    location_transfers: int
    user_transfers: int
    total_assets_transferred: int
    recent_transfers: List[RecentTransferResponse]
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================
# 📱 MY TRANSFERS SCHEMA
# ============================================================

class MyTransferResponse(BaseModel):
    """
    Schema for my transfers response (mobile).
    """
    id: UUID
    transfer_type: TransferType
    reason: Optional[str] = None
    remarks: Optional[str] = None
    transferred_by: Optional[str] = None
    transferred_by_id: Optional[UUID] = None
    asset_count: int
    created_at: datetime
    is_initiated_by_me: Optional[bool] = False
    is_received_by_me: Optional[bool] = False
    is_sent_by_me: Optional[bool] = False

    class Config:
        from_attributes = True


# ============================================================
# 📄 REPORT SCHEMA
# ============================================================

class TransferReportResponse(BaseModel):
    """
    Schema for transfer report.
    """
    id: UUID
    transfer_type: TransferType
    reason: Optional[str] = None
    remarks: Optional[str] = None
    transferred_by: Optional[str] = None
    transferred_by_id: Optional[UUID] = None
    created_at: datetime
    assets: List[TransferAssetDetailResponse]
    report_generated_at: datetime
    report_generated_by: str

    class Config:
        from_attributes = True