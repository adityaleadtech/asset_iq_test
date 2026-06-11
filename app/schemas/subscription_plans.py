from pydantic import BaseModel
class SubscriptionPlanCreate(BaseModel):
    name: str
    # REMOVED: max_users: int
    max_assets: int
    max_locations: int = 1
    price_monthly: float | None = None
    price_annually: float | None = None
    features_json: dict | None = None


class SubscriptionPlanResponse(BaseModel):
    id: str
    name: str
    # REMOVED: max_users: int
    max_assets: int
    max_locations: int
    price_monthly: float | None
    price_annually: float | None
    features_json: str | None
    is_active: bool

    model_config = {
        "from_attributes": True
    }


class SubscriptionPlanUpdate(BaseModel):
    name: str | None = None
    # REMOVED: max_users: int | None = None
    max_assets: int | None = None
    max_locations: int | None = None
    price_monthly: float | None = None
    price_annually: float | None = None
    features_json: dict | None = None





from pydantic import BaseModel
from typing import Optional
from datetime import datetime


from datetime import datetime
from pydantic import BaseModel


class SubscriptionStatusResponse(
    BaseModel
):

    client_id: str

    subscribed: bool

    subscription_id: str | None = None

    plan_name: str | None = None

    status: str | None = None

    expires_at: datetime | None = None