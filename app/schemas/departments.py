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

    manager_id: Optional[str] = None


class DepartmentUpdate(
    BaseModel
):
    parent_department_id: Optional[str] = None

    name: Optional[str] = None

    code: Optional[str] = None

    description: Optional[str] = None

    manager_id: Optional[str] = None


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

    class Config:
        from_attributes = True

