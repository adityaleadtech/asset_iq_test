from pydantic import BaseModel, Field


class Profile(BaseModel):
    id: str
    full_name: str
    department_name: str | None = None
    role: str
    phone: str | None = None
    email: str
    profile_photo_url: str | None = None
    is_active: bool
    subscribed: bool
    services: list[str] = Field(
        default_factory=list
    )

    model_config = {
        "from_attributes": True
    }