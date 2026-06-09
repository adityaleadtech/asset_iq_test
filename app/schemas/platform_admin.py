from pydantic import BaseModel,EmailStr
from datetime import datetime


class PlatformAdminResponse(BaseModel):
    id:str
    email:str
    full_name:str
    is_active:bool
    created_at:datetime
    role:str
   

    model_config={
        "from_attributes":True
    }


class PlatformAdminLogin(BaseModel):
    email:EmailStr
    password:str


class PlatformAdminCreation(BaseModel):
    full_name:str
    email:str
    password_hash:str
    role:str


class TokenResponse(BaseModel):
    access_token:str
    token_type:str
