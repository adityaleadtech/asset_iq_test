from pydantic import BaseModel
from typing import Optional


class ServiceCreate(BaseModel):

    code: str

    name: str

    description: Optional[str] = None


class ServiceResponse(BaseModel):

    id: str

    code: str

    name: str

    description: Optional[str]

    is_active: bool

    model_config = {
        "from_attributes": True
    }



from pydantic import BaseModel
from typing import Optional


class ServiceUpdate(BaseModel):

    code: Optional[str] = None

    name: Optional[str] = None

    description: Optional[str] = None