from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class ScanAssetRequest(BaseModel):
    asset_id: str


class AuditPlanCreate(BaseModel):
    name: str
    description: Optional[str] = None
    client_id: Optional[str] = None
    auditor_id: str
    frequency_unit: str
    frequency_interval: int
    start_date: datetime
    end_date: datetime
    targets: List["AuditTargetCreate"]


class AuditTargetCreate(BaseModel):
    target_type: str
    target_id: str


class AuditPlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    auditor_id: Optional[str] = None
    frequency_unit: Optional[str] = None
    frequency_interval: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None


class AuditSessionResponse(BaseModel):
    id: str
    audit_plan_id: Optional[str] = None
    audit_name: Optional[str] = None
    scheduled_date: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str
    assigned_to: str
    assigned_to_name: Optional[str] = None
    conducted_by: Optional[str] = None
    total_assets: int
    audited_assets: int

    class Config:
        from_attributes = True


class AuditPlanResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    auditor_id: str
    auditor_name: str
    frequency_unit: str
    frequency_interval: int
    start_date: datetime
    end_date: datetime
    next_run_date: Optional[datetime] = None
    status: str
    created_at: datetime
    sessions: Optional[List[AuditSessionResponse]] = None
    sessions_count: Optional[int] = None

    class Config:
        from_attributes = True


class AuditPlanListResponse(BaseModel):
    items: List[AuditPlanResponse]
    total: int
    page: int
    size: int


class AuditSessionListResponse(BaseModel):
    items: List[AuditSessionResponse]
    total: int
    page: int
    size: int


class AuditDashboardResponse(BaseModel):
    total_audits: int
    active_audits: int
    completed_sessions: int
    pending_sessions: int
    in_progress_sessions: int
    total_assets: int
    audited_assets: int


class MyAuditResponse(BaseModel):
    audit_id: str
    session_id: str
    audit_name: str
    status: str
    start_date: datetime
    end_date: datetime
    scheduled_date: datetime
    total_assets: int
    audited_assets: int
    completion_percentage: float


class AuditAssetResponse(BaseModel):
    asset_id: str
    asset_name: str
    serial_number: Optional[str] = None
    qr_code_url: Optional[str] = None
    location: Optional[str] = None
    audit_status: str


class AuditDetailsResponse(BaseModel):
    audit_id: str
    session_id: str
    audit_name: str
    description: Optional[str] = None
    status: str
    scheduled_date: datetime
    start_date: datetime
    end_date: datetime
    total_assets: int
    audited_assets: int
    completion_percentage: float
    assets: List[AuditAssetResponse]


class ScanAssetResponse(BaseModel):
    asset_id: str
    asset_name: str
    serial_number: Optional[str] = None
    qr_code_url: Optional[str] = None
    location: Optional[str] = None
    expected_condition: Optional[str] = None
    already_audited: bool = False


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


class AuditAssetDetailsResponse(BaseModel):
    asset_id: str
    asset_name: str
    asset_code: Optional[str] = None
    serial_number: Optional[str] = None
    category: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    expected_quantity: Optional[int] = None
    expected_condition: Optional[str] = None
    image_url: Optional[str] = None


class AuditSummaryResponse(BaseModel):
    audit_id: str
    session_id: str
    audit_name: str
    status: str
    total_assets: int
    audited_assets: int
    remaining_assets: int
    completion_percentage: float
    in_place: int
    dislocated: int
    not_found: int
    lost: int


class AuditReviewAsset(BaseModel):
    asset_id: str
    asset_code: Optional[str] = None
    asset_name: str
    department: Optional[str] = None
    location: Optional[str] = None
    status: str
    remarks: Optional[str] = None


class AuditReviewResponse(BaseModel):
    audit_id: str
    session_id: str
    total_assets: int
    completed_assets: int
    pending_assets: int
    assets: List[AuditReviewAsset]


class AuditReportInformation(BaseModel):
    report_id: str
    generated_at: datetime
    generated_by: str


class AuditInformation(BaseModel):
    audit_id: str
    audit_code: Optional[str] = None
    audit_name: str
    audit_status: str
    audit_type: Optional[str] = None
    target_name: Optional[str] = None
    scheduled_date: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    audit_duration: Optional[str] = None


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
    serial_number: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    category: Optional[str] = None
    asset_type: Optional[str] = None
    department: Optional[str] = None
    expected_location: Optional[str] = None
    audited_location: Optional[str] = None
    audit_status: str
    condition_status: Optional[str] = None
    quantity_expected: Optional[int] = None
    quantity_found: Optional[int] = None
    location_status: Optional[str] = None
    audited_by: Optional[str] = None
    audited_at: Optional[datetime] = None
    remarks: Optional[str] = None
    created_image_url: Optional[str] = None
    latest_image_url: Optional[str] = None
    audit_image_url: Optional[str] = None
    expected_latitude: Optional[float] = None
    expected_longitude: Optional[float] = None
    audit_latitude: Optional[float] = None
    audit_longitude: Optional[float] = None


class AuditReportResponse(BaseModel):
    report_information: AuditReportInformation
    audit_information: AuditInformation
    audit_summary: AuditSummary
    asset_verification_details: List[AssetVerificationDetail]


AuditPlanCreate.model_rebuild()


from typing import List, Optional
from pydantic import BaseModel

from app.enums.audit_enums import AuditResultStatus


class AuditReviewAsset(BaseModel):
    asset_id: str
    asset_code: Optional[str] = None
    asset_name: str
    department: Optional[str] = None
    location: Optional[str] = None
    status: AuditResultStatus
    remarks: Optional[str] = None


class AuditReviewResponse(BaseModel):
    audit_id: str
    session_id: str
    total_assets: int
    completed_assets: int
    pending_assets: int
    completion_percentage: float
    assets: List[AuditReviewAsset]
