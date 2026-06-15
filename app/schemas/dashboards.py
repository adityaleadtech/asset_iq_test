from pydantic import BaseModel


class SubscriptionSummary(
    BaseModel
):
    max_assets: int

    max_departments: int

    licence_count: int

    used_licences: int


class ClientDashboardResponse(
    BaseModel
):
    total_users: int

    active_users: int

    total_departments: int

    total_assets: int

    subscription: SubscriptionSummary