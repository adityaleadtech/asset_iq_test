from pydantic import BaseModel, EmailStr


class AssignManagerRequest(BaseModel):

    manager_id: str

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


class ManagerUpdate(BaseModel):

    department_id: str | None = None

    full_name: str | None = None

    phone: str | None = None

    employee_id: str | None = None




from pydantic import BaseModel


class UserServicePermission(
    BaseModel
):

    service_id: str

    can_create: bool = False

    can_read: bool = False

    can_update: bool = False

    can_delete: bool = False



class UserRoleCreate(
    BaseModel
):

    name: str

    description: str | None = None

    permissions: list[
        UserServicePermission
    ]


class UserCreate(BaseModel):

    client_id: str | None = None

    full_name: str

    email: str

    password: str

    phone: str | None = None

    employee_id: str | None = None

    department_id: str | None = None

    role: UserRoleCreate


class UserResponse(
    BaseModel
):

    id: str

    client_id: str

    custom_role_id: str | None

    email: str

    full_name: str

    phone: str | None

    employee_id: str | None

    department_id: str | None

    role: str

    is_active: bool

    model_config = {
        "from_attributes": True
    }



class UserUpdate(
    BaseModel
):

    full_name: str | None = None

    phone: str | None = None

    employee_id: str | None = None

    department_id: str | None = None

    role: UserRoleCreate | None = None