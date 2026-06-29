from datetime import date, datetime
from decimal import Decimal
from fastapi import HTTPException
from pydantic import BaseModel

from app.models.maintenance_task import MaintenanceTask


class AssetCreate(BaseModel):
    category_id: str
    type_id: str
    department_id: str
    name: str
    description: str | None = None
    serial_number: str | None = None
    model: str | None = None
    manufacturer: str | None = None
    purchase_date: date | None = None
    purchase_value: Decimal | None = None
    assigned_to_user_id: str | None = None
    created_image_url: str | None = None
    custom_fields: list[CustomField] = []
    location_id: str | None = None
    

class AssetUpdate(BaseModel):
    category_id: str | None = None
    type_id: str | None = None
    department_id: str | None = None
    name: str | None = None
    description: str | None = None
    serial_number: str | None = None
    model: str | None = None
    manufacturer: str | None = None
    purchase_date: date | None = None
    purchase_value: Decimal | None = None
    assigned_to_user_id: str | None = None
    custom_fields: list[CustomField] = []
    location_id: str | None = None  # ADD THIS

class AssetResponse(BaseModel):
    id: str
    client_id: str
    category_id: str | None
    type_id: str | None
    department_id: str | None
    assigned_to_user_id: str | None
    name: str
    description: str | None
    serial_number: str | None
    model: str | None
    manufacturer: str | None
    purchase_date: date | None
    purchase_value: Decimal | None
    asset_condition: str  # ACTIVE, MAINTENANCE, RETIRED, LOST
    tag_state: str  # NOT_TAGGED, TAGGED, VERIFIED
    is_active: bool
    qr_code_url: str | None = None
    created_image_url: str | None = None
    latest_image_url: str | None = None
    current_latitude: float | None = None
    current_longitude: float | None = None
    last_scanned_by: str | None = None
    last_scanned_at: datetime | None = None
    location_id: str | None = None
    remarks: str | None = None
    location: LocationDetails | None = None
    custom_fields: list[CustomField] = []

    created_by: str | None = None



    model_config = {
        "from_attributes": True
    }



class AssetAssignRequest(BaseModel):
    user_id: str


class AssetVerificationResponse(BaseModel):
    asset_id: str
    asset_condition: str
    tag_state: str
    current_latitude: float | None = None
    current_longitude: float | None = None
    latest_image_url: str | None = None
    remarks: str | None = None
    last_scanned_at: datetime | None = None

# app/schemas/assets.py

class AssetVerificationRequest(BaseModel):
    latitude: float
    longitude: float
    asset_condition: str
    remarks: str | None = None
    image_url: str | None = None




from datetime import datetime
from pydantic import BaseModel


class AssetAuditResponse(BaseModel):
    id: str
    asset_id: str

    latitude: float | None = None
    longitude: float | None = None

    image_url: str | None = None
    notes: str | None = None

    asset_condition: str | None = None
    tag_state: str | None = None

    scanned_by: str | None = None
    scanned_at: datetime | None = None

    class Config:
        from_attributes = True



from datetime import datetime
from pydantic import BaseModel


class AssetAuditResponse(BaseModel):
    id: str
    asset_id: str

    latitude: float | None = None
    longitude: float | None = None

    image_url: str | None = None
    remarks: str | None = None

    asset_condition: str | None = None
    tag_state: str | None = None

    scanned_by: str
    scanned_at: datetime

    class Config:
        from_attributes = True



class AssetVerificationFormResponse(BaseModel):
    asset_id: str
    name: str
    manufacturer: str | None = None
    serial_number: str | None = None
    model: str | None = None
    purchase_value: float | None = None

    tag_state: str
    asset_condition: str

    department_name: str | None = None
    created_image_url: str | None = None

    class Config:
        from_attributes = True


from pydantic import BaseModel
from decimal import Decimal


class AssetVerificationFormResponse(BaseModel):
    asset_id: str
    name: str
    manufacturer: str | None = None
    serial_number: str | None = None
    model: str | None = None
    purchase_value: Decimal | None = None

    asset_condition: str
    tag_state: str

    category_name: str | None = None
    type_name: str | None = None
    department_name: str | None = None

    created_image_url: str | None = None
    latest_image_url: str | None = None
    qr_code_url: str | None = None

    current_latitude: float | None = None
    current_longitude: float | None = None

    class Config:
        from_attributes = True


from datetime import datetime
from pydantic import BaseModel


class AssetLocationResponse(BaseModel):
    asset_id: str
    latitude: float | None = None
    longitude: float | None = None

    tag_state: str
    asset_condition: str

    last_scanned_by: str | None = None
    last_scanned_at: datetime | None = None

    class Config:
        from_attributes = True



class AssetQrResponse(BaseModel):
    asset_id: str
    asset_name: str
    qr_code_url: str | None
    tag_state: str

    class Config:
        from_attributes = True



class AssetQrResponse(BaseModel):
    asset_id: str
    asset_name: str
    qr_code_url: str | None
    tag_state: str

    class Config:
        from_attributes = True


class AssetDashboardResponse(BaseModel):
    total_assets: int
    tagged_assets: int
    not_tagged_assets: int
    active_assets: int
    inactive_assets: int
    damaged_assets: int
    maintenance_assets: int
    lost_assets: int



class LocationPathItem(BaseModel):
    id: str
    name: str
    location_type: str


class LocationDetails(BaseModel):
    id: str
    path: list[LocationPathItem]



class AssetBulkItem(BaseModel):
    category: str
    type: str

    department: str | None = None
    location: str | None = None

    name: str
    description: str | None = None
    serial_number: str | None = None
    model: str | None = None
    manufacturer: str | None = None

    purchase_value: float | None = None

    created_image_url: str | None = None
    latest_image_url: str | None = None


class AssetBulkCreate(BaseModel):
    assets: list[AssetBulkItem]

from typing import Union
from pydantic import BaseModel


class CustomField(BaseModel):
    name: str
    type: str = "TEXT"
    value: Union[
        str,
        int,
        float,
        bool,
        None
    ] = None



class AssetConditionStatsResponse(BaseModel):
    ACTIVE: int
    INACTIVE: int
    DAMAGED: int
    UNDER_MAINTENANCE: int
    LOST: int


class AssetTaggingStatsResponse(BaseModel):
    TAGGED: int
    NOT_TAGGED: int


class AssetSearchResponse(BaseModel):
    items: list[AssetResponse]
    page: int
    limit: int
    total: int
    total_pages: int



from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date

class PaginationMeta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int
    has_next: bool
    has_previous: bool

class AssetResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    model: Optional[str]
    manufacturer: Optional[str]
    serial_number: Optional[str]
    asset_tag: Optional[str]
    asset_condition: str
    tag_state: str
    purchase_date: Optional[date]
    purchase_cost: Optional[float]
    warranty_expiry: Optional[date]
    last_scanned_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    category_id: Optional[str]
    type_id: Optional[str]
    department_id: Optional[str]
    location_id: Optional[str]
    assigned_to_user_id: Optional[str]
    client_id: str
    
    # Nested relations (optional)
    category: Optional['CategoryResponse']
    type: Optional['TypeResponse']
    department: Optional['DepartmentResponse']
    location: Optional['LocationResponse']
    assigned_to: Optional['UserResponse']

    class Config:
        from_attributes = True

class AssetSearchResponse(BaseModel):
    items: List[AssetResponse]
    pagination: PaginationMeta



from pydantic import BaseModel
from typing import Optional


class CategoryResponse(BaseModel):
    id: str
    name: str

    class Config:
        from_attributes = True


class TypeResponse(BaseModel):
    id: str
    name: str

    class Config:
        from_attributes = True


class DepartmentResponse(BaseModel):
    id: str
    name: str

    class Config:
        from_attributes = True


class LocationResponse(BaseModel):
    id: str
    name: str
    location_type: str
    code: Optional[str] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    address_line_3: Optional[str] = None
    postal_code: Optional[str] = None

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: str
    full_name: Optional[str] = None
    email: str
    employee_id: Optional[str] = None
    role: str

    class Config:
        from_attributes = True

class AssetResponse(BaseModel):
    id: str
    client_id: str
    category_id: Optional[str] = None
    type_id: Optional[str] = None
    department_id: Optional[str] = None
    location_id: Optional[str] = None
    assigned_to_user_id: Optional[str] = None

    name: str
    description: Optional[str] = None
    serial_number: Optional[str] = None
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    purchase_date: Optional[date] = None
    purchase_value: Optional[Decimal] = None

    asset_condition: str
    tag_state: str

    qr_code_url: Optional[str] = None
    created_image_url: Optional[str] = None
    latest_image_url: Optional[str] = None

    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None
    last_scanned_by: Optional[str] = None
    last_scanned_at: Optional[datetime] = None
    remarks: Optional[str] = None
    created_by: Optional[str] = None
    is_active: bool

    # Nested objects
    category: Optional[CategoryResponse] = None
    type: Optional[TypeResponse] = None
    department: Optional[DepartmentResponse] = None
    location: Optional[LocationResponse] = None
    assigned_to: Optional[UserResponse] = None

    class Config:
        from_attributes = True


from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AssetTimelineResponse(BaseModel):
    event_type: str
    title: str
    description: Optional[str] = None
    performed_by: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MarkLostRequest(BaseModel):
    reason: str
    notes: str | None = None



from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AssetTimelineItem(BaseModel):
    event_type: str
    title: str
    description: Optional[str]
    performed_by: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

from datetime import date
from pydantic import BaseModel
from typing import Optional



from decimal import Decimal
from pydantic import BaseModel
from typing import Optional, List




class CreateMaintenanceRequest(
    BaseModel
):
    issue_description: str
    photos_urls: list[str] = []
    estimated_cost: Decimal | None = None
    is_emergency: bool = False
    vendor_name: str | None = None



class MaintenanceTaskResponse(
    BaseModel
):
    id: str
    asset_id: str
    client_id: str
    raised_by: str
    issue_description: str

    photos_urls: list[str] = []

    estimated_cost: Decimal | None = None
    is_emergency: bool
    status: str

    approved_by: str | None = None
    approved_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    vendor_name: str | None = None
    parts_replaced: list[str] = []

    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class RejectMaintenanceRequest(
    BaseModel
):
    rejection_reason: str