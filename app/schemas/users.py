from pydantic import BaseModel, EmailStr


class ClientAdminCreate(BaseModel):
    client_id: str
    email: EmailStr
    password: str
    full_name: str
    phone: str | None = None


class UserResponse(BaseModel):

    id: str

    client_id: str

    email: str

    full_name: str

    phone: str | None

    role: str

    is_active: bool

    model_config = {
        "from_attributes": True
    }



class ClientAdminLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class ClientAdminProfileResponse(BaseModel):

    id: str

    client_id: str

    email: str

    full_name: str

    phone: str | None

    role: str

    is_active: bool

    model_config = {
        "from_attributes": True
    }


from pydantic import BaseModel
from pydantic import EmailStr


class ManagerCreate(BaseModel):

    client_id: str | None = None

    department_id: str | None = None

    email: EmailStr

    password: str

    full_name: str

    phone: str | None = None

    employee_id: str | None = None


class UserResponse(BaseModel):

    id: str

    client_id: str

    department_id: str | None

    email: str

    full_name: str

    phone: str | None

    role: str

    employee_id: str | None

    is_active: bool

    model_config = {
        "from_attributes": True
    }