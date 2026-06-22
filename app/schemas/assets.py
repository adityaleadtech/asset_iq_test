from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel


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
    remarks: str | None = None
    created_by: str | None = None

    class Config:
        from_attributes = True


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