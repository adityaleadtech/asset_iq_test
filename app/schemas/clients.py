from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
import re

class ClientCreate(BaseModel):
    name: str
    industry: str | None = None
    contact_email: str
    contact_phone: str | None = None
    address_line_1: str
    address_line_2: str | None = None
    address_line_3: str | None = None
    logo_url: str | None = None
    # Note: client_code is NOT in request body

class ClientResponse(BaseModel):
    id: str
    client_code: str  # This will be returned in response
    name: str
    industry: str | None
    contact_email: str
    contact_phone: str | None
    address: str | None
    logo_url: str | None
    is_active: bool
    created_by_admin_id: str | None
    created_at: datetime
    updated_at: datetime | None
    address_line_1: str | None = None
    address_line_2: str | None = None
    address_line_3: str | None = None
    
    model_config = {
        "from_attributes": True
    }

class ClientUpdate(BaseModel):
    name: str | None = None
    industry: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    address_line_1: str | None = None
    address_line_2: str | None = None
    address_line_3: str | None = None
    logo_url: str | None = None
    is_active: bool | None = None
    # Note: client_code cannot be updated