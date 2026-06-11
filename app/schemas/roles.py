from pydantic import BaseModel
from typing import Optional


class RoleCreate(BaseModel):

    name: str

    description: Optional[str] = None

class RoleUpdate(BaseModel):

    name: Optional[str] = None

    description: Optional[str] = None

class RoleResponse(BaseModel):

    id: str

    client_id: str

    name: str

    description: Optional[str]

    is_active: bool

    model_config = {
        "from_attributes": True
    }


class RoleUpdate(BaseModel):

    name: str | None = None

    description: str | None = None