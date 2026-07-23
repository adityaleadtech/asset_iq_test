from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.enums.audit_enums import (
    AuditFrequencyUnit,
    AuditLocationStatus,
    AuditPlanStatus,
    AuditSessionStatus,
    AuditTargetType,
    AuditAssetStatus,
    AuditConditionStatus,
    AuditResultStatus,  # ✅ ADDED
)
from datetime import date
from pydantic import BaseModel, ConfigDict


class AuditAssetResponse(BaseModel):
    asset_id: str
    asset_name: str
    serial_number: str | None = None
    qr_code_url: str | None = None
    location: str | None = None
    audit_status: str

    model_config = ConfigDict(from_attributes=True)


class AuditDetailsResponse(BaseModel):
    audit_id: str
    session_id: str
    audit_name: str
    description: str | None = None

    status: str

    scheduled_date: date
    start_date: date
    end_date: date | None = None

    total_assets: int
    audited_assets: int
    completion_percentage: float

    assets: list[AuditAssetResponse]

    model_config = ConfigDict(from_attributes=True)

class AuditAssetResponse(BaseModel):
    asset_id: str
    asset_name: str
    serial_number: str | None
    qr_code_url: str | None
    location: str | None
    audit_status: str

    model_config = ConfigDict(from_attributes=True)



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
# Audit Session Response
# ==========================================================

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
# Audit Plan Response
# ==========================================================

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
# Audit Asset Request (Used by Mobile App)
# ==========================================================

class AuditResultRequest(BaseModel):
    status: AuditAssetStatus
    condition_status: Optional[AuditConditionStatus] = None
    quantity_found: int = Field(default=1, ge=0)
    remarks: Optional[str] = None
    audit_latitude: Decimal
    audit_longitude: Decimal

class MyAuditResponse(BaseModel):
    audit_id: str
    session_id: str
    audit_name: str
    status: str
    start_date: date
    end_date: date | None
    scheduled_date: date
    total_assets: int
    audited_assets: int
    completion_percentage: float

    model_config = ConfigDict(from_attributes=True)

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
    status: AuditResultStatus  # ✅ Now works with imported enum
    condition_status: Optional[AuditConditionStatus] = None
    quantity_expected: int
    quantity_found: int
    remarks: Optional[str] = None
    photo_url: Optional[str] = None
    expected_location_id: Optional[str] = None
    expected_latitude: Optional[Decimal] = None
    expected_longitude: Optional[Decimal] = None
    audit_latitude: Optional[Decimal] = None
    audit_longitude: Optional[Decimal] = None
    location_status: AuditLocationStatus
    audited_by: Optional[str] = None
    audited_at: Optional[datetime] = None


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




class ScanAssetRequest(BaseModel):
    asset_id: str


class SubmitAssetAuditRequest(BaseModel):
    status: AuditResultStatus
    condition_status: str | None = None
    quantity_found: int = 1
    remarks: str | None = None
    audit_latitude: float | None = None
    audit_longitude: float | None = None
    photo_url: str | None = None

class SubmitAssetAuditRequest(BaseModel):
    status: AuditResultStatus
    condition_status: str | None = None
    quantity_found: int = 1
    remarks: str | None = None
    audit_latitude: float | None = None
    audit_longitude: float | None = None
    photo_url: str | None = None


class SubmitAssetAuditResponse(BaseModel):
    message: str

    audit_id: str
    session_id: str

    asset_id: str
    asset_name: str

    audited_assets: int
    total_assets: int
    remaining_assets: int

    completion_percentage: float

    is_complete: bool

    model_config = ConfigDict(from_attributes=True)

class ScanAssetResponse(BaseModel):
    success: bool
    message: str
    asset_id: str



class AuditAssetDetailsResponse(BaseModel):
    asset_id: str

    name: str | None=None
    description: str | None = None

    serial_number: str | None = None

    manufacturer: str | None = None
    model: str | None = None

    category: str | None = None
    asset_type: str | None = None
    department: str | None = None
    location: str | None = None

    current_condition: str | None = None

    qr_code_url: str | None = None
    barcode_url: str | None = None

    latest_image_url: str | None = None

    current_latitude: float | None = None
    current_longitude: float |None = None

class AuditSummaryResponse(BaseModel):
    audit_id: str
    session_id: str
    audit_name: str

    status: AuditSessionStatus

    total_assets: int
    audited_assets: int
    remaining_assets: int

    completion_percentage: float

    in_place: int
    dislocated: int
    not_found: int
    lost: int


# ==========================================================
# Audit Report
# ==========================================================

class AuditReportInformation(BaseModel):
    report_id: str
    generated_at: datetime
    generated_by: str


class AuditInformation(BaseModel):
    audit_id: str
    audit_code: str
    audit_name: str

    audit_status: AuditSessionStatus

    audit_type: AuditTargetType

    target_name: str | None = None

    scheduled_date: date
    started_at: datetime | None = None
    completed_at: datetime | None = None

    audit_duration: str | None = None


class AuditSummary(BaseModel):
    total_assets: int

    audited_assets: int
    pending_assets: int

    verified_assets: int
    dislocated_assets: int
    lost_assets: int
    not_found_assets: int

    completion_percentage: float
    verification_percentage: float


class AssetVerificationDetail(BaseModel):
    asset_id: str

    asset_code: str
    asset_name: str

    serial_number: str | None = None

    manufacturer: str | None = None
    model: str | None = None

    category: str | None = None
    asset_type: str |None = None

    department: str | None = None

    expected_location: str | None = None
    audited_location: str | None = None

    audit_status: AuditResultStatus

    condition_status: AuditConditionStatus | None = None

    quantity_expected: int
    quantity_found: int

    location_status: AuditLocationStatus

    audited_by: str | None = None
    audited_at: datetime | None = None

    remarks: str | None = None

    created_image_url: str | None = None
    latest_image_url: str | None = None
    audit_image_url: str | None = None

    expected_latitude: Decimal | None = None
    expected_longitude: Decimal | None = None

    audit_latitude: Decimal | None = None
    audit_longitude: Decimal | None = None


class AuditReportResponse(BaseModel):
    report_information: AuditReportInformation

    audit_information: AuditInformation

    audit_summary: AuditSummary

    asset_verification_details: list[AssetVerificationDetail]