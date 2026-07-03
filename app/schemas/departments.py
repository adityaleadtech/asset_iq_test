from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DepartmentCreate(
    BaseModel
):
    parent_department_id: Optional[str] = None

    name: str

    code: Optional[str] = None

    description: Optional[str] = None
    location_id: str | None = None
    manager_id: Optional[str] = None


class DepartmentUpdate(
    BaseModel
):
    parent_department_id: Optional[str] = None

    name: Optional[str] = None

    code: Optional[str] = None

    description: Optional[str] = None

    manager_id: Optional[str] = None

    location_id: str | None = None  # ADD THIS

    is_active: Optional[bool] = None

class DepartmentResponse(
    BaseModel
):
    id: str

    client_id: str

    parent_department_id: Optional[str] = None

    name: str

    code: Optional[str] = None

    description: Optional[str] = None

    manager_id: Optional[str] = None

    is_active: bool

    created_at: datetime

    updated_at: datetime
    location_id: str | None = None



    model_config = {
        "from_attributes": True
    }
    

class LocationPathItem(BaseModel):
    id: str
    name: str
    location_type: str


class LocationDetails(BaseModel):
    id: str
    path: list[LocationPathItem]

