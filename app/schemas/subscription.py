from datetime import date

from pydantic import BaseModel


class SubscriptionCreate(BaseModel):

    plan_id: str

    licence_count: int

    billing_cycle: str

    starts_at: date

    ends_at: date | None = None

    auto_renew: bool = True



class SubscriptionResponse(BaseModel):

    id: str

    client_id: str

    plan_id: str

    status: str

    licence_count: int

    used_licences: int

    billing_cycle: str

    starts_at: date

    ends_at: date | None

    auto_renew: bool

    model_config = {
        "from_attributes": True
    }

class SubscriptionUpdate(BaseModel):

    plan_id: str | None = None

    licence_count: int | None = None

    billing_cycle: str | None = None

    ends_at: date | None = None

    auto_renew: bool | None = None


