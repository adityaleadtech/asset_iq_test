from pydantic import BaseModel, EmailStr




class ClientCreate(BaseModel):

    name: str

    industry: str | None = None

    contact_email: str

    contact_phone: str | None = None

    address_line_1: str

    address_line_2: str | None = None

    address_line_3: str | None = None

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


class ClientUpdate(BaseModel):

    name: str | None = None

    industry: str | None = None

    contact_email: str | None = None

    contact_phone: str | None = None

    address_line_1: str | None = None

    address_line_2: str | None = None

    address_line_3: str | None = None