from pydantic import BaseModel, EmailStr


# ==========================================
# LOGIN REQUEST
# ==========================================

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ==========================================
# USER DETAILS
# ==========================================

class LoggedInUser(BaseModel):
    id: str

    name: str

    email: EmailStr

    role: str

    client_id: str | None = None

    department_id: str | None = None

    custom_role_id: str | None = None

    designation: str | None = None


# ==========================================
# PERMISSION
# ==========================================

class PermissionResponse(BaseModel):
    service_code: str

    actions: list[str]


# ==========================================
# LOGIN RESPONSE
# ==========================================

class LoginResponse(BaseModel):
    access_token: str

    token_type: str = "bearer"


    user: LoggedInUser

