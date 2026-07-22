from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from app.enums.audit_enums import (
    AuditFrequencyUnit,
    AuditLocationStatus,
    AuditPlanStatus,
    AuditSessionStatus,
    AuditTargetType,
    AuditAssetStatus,
    AuditConditionStatus
)


# ==========================================================
# Audit Target
# ==========================================================

class AuditTargetRequest(BaseModel):
    target_type: AuditTargetType
    target_id: str


class AuditTargetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    target_type: AuditTargetType
    target_id: str


# ==========================================================
# Create Audit Plan
# ==========================================================

class AuditPlanCreate(BaseModel):

    client_id: Optional[str] = None

    name: str = Field(..., max_length=255)

    description: Optional[str] = None

    auditor_id: str

    frequency_unit: AuditFrequencyUnit

    frequency_interval: int = Field(..., ge=1)

    start_date: date

    end_date: Optional[date] = None

    targets: list[AuditTargetRequest]

# ==========================================================
# Update Audit Plan
# ==========================================================

class AuditPlanUpdate(BaseModel):

    name: Optional[str] = Field(None, max_length=255)

    description: Optional[str] = None

    auditor_id: Optional[str] = None

    frequency_unit: Optional[AuditFrequencyUnit] = None

    frequency_interval: Optional[int] = Field(None, ge=1)

    start_date: Optional[date] = None

    end_date: Optional[date] = None

    status: Optional[AuditPlanStatus] = None

    targets: Optional[list[AuditTargetRequest]] = None


# ==========================================================
# Audit Plan Response
# ==========================================================
from typing import List, Optional

class AuditPlanResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str]
    auditor_id: str
    auditor_name: str
    frequency_unit: AuditFrequencyUnit
    frequency_interval: int
    start_date: date
    end_date: Optional[date]
    next_run_date: date
    status: AuditPlanStatus
    created_at: datetime

    sessions: List[AuditSessionResponse] = []
# ==========================================================
# Audit Session Response
# ==========================================================

from datetime import date, datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID

    scheduled_date: date

    status: str

    assigned_to: UUID

    started_at: Optional[datetime] = None

    completed_at: Optional[datetime] = None

    total_assets: int

    audited_assets: int
    tracking_session_id: str | None = None
# ==========================================================
# Audit Asset Request
# Used by Mobile App
# ==========================================================

class AuditResultRequest(BaseModel):

    status: AuditAssetStatus

    condition_status: Optional[AuditConditionStatus] = None

    quantity_found: int = Field(default=1, ge=0)

    remarks: Optional[str] = None

    audit_latitude: Decimal

    audit_longitude: Decimal


class MyAuditSessionResponse(BaseModel):
    id: UUID

    audit_plan_id: UUID

    audit_name: str

    scheduled_date: date

    status: AuditSessionStatus

    total_assets: int

    audited_assets: int

    started_at: Optional[datetime] = None

    completed_at: Optional[datetime] = None

    created_at: datetime

    assigned_to: UUID
# ==========================================================
# Audit Result Response
# ==========================================================

class AuditResultResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    asset_id: str

    asset_name: str

    serial_number: str

    status: AuditAssetStatus

    condition_status: Optional[AuditConditionStatus]

    quantity_expected: int

    quantity_found: int

    remarks: Optional[str]

    photo_url: Optional[str]

    expected_location_id: Optional[str]

    expected_latitude: Optional[Decimal]

    expected_longitude: Optional[Decimal]

    audit_latitude: Optional[Decimal]

    audit_longitude: Optional[Decimal]

    location_status: AuditLocationStatus

    audited_by: str

    audited_at: datetime


# ==========================================================
# Dashboard
# ==========================================================

class AuditDashboardResponse(BaseModel):

    total_audits: int

    active_audits: int

    completed_sessions: int

    pending_sessions: int

    in_progress_sessions: int

    total_assets: int

    audited_assets: int

# ==========================================================
# Audit Plan List Response
# ==========================================================

class AuditPlanListResponse(BaseModel):

    total: int

    page: int

    size: int

    items: list[AuditPlanResponse]


# ==========================================================
# Audit Session List Response
# ==========================================================

class AuditSessionListResponse(BaseModel):

    total: int

    page: int

    size: int

    items: list[AuditSessionResponse]