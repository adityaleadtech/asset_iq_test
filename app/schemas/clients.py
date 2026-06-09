from pydantic import BaseModel, EmailStr


class ClientCreate(BaseModel):
    name: str
    industry: str | None = None
    contact_email: EmailStr
    contact_phone: str | None = None
    address: str | None = None
    logo_url: str | None = None


class ClientResponse(BaseModel):
    id: str
    name: str
    industry: str | None
    contact_email: str
    contact_phone: str | None
    address: str | None
    logo_url: str | None
    is_active: bool

    model_config = {
        "from_attributes": True
    }