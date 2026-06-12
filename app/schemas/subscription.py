from datetime import date

from pydantic import BaseModel


class SubscriptionCreate(
    BaseModel
):

    licence_count: int

    max_assets: int

    max_departments: int

    price: float

    starts_at: date

    ends_at: date

    auto_renew: bool

    services: list[str]


class SubscriptionUpdate(
    BaseModel
):

    licence_count: int | None = None

    max_assets: int | None = None

    max_departments: int | None = None

    price: float | None = None

    starts_at: date | None = None

    ends_at: date | None = None

    auto_renew: bool | None = None

    services: list[str] | None = None


class SubscriptionResponse(
    BaseModel
):

    id: str

    client_id: str

    licence_count: int

    used_licences: int

    max_assets: int

    max_departments: int

    price: float

    status: str

    starts_at: date

    ends_at: date

    auto_renew: bool

    class Config:

        from_attributes = True





class ServiceSummary(
    BaseModel
):

    id: str

    code: str

    name: str


class SubscriptionDetailsResponse(
    BaseModel
):

    id: str

    client_id: str

    licence_count: int

    used_licences: int

    max_assets: int

    max_departments: int

    price: float

    status: str

    starts_at: date

    ends_at: date

    auto_renew: bool

    services: list[ServiceSummary]

    class Config:

        from_attributes = True