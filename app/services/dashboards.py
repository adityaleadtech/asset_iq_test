from fastapi import HTTPException

from app.models.users import User
from app.models.departments import Department
from app.models.asset import Asset
from app.models.subscription import Subscription
from app.schemas.dashboards import (
    ClientDashboardResponse,
    SubscriptionSummary
);
def get_client_dashboard(
    db,
    current_user,
    client_id: str | None = None
):

    if current_user["role"] == "ADMIN":

        if not client_id:
            raise HTTPException(
                status_code=400,
                detail="client_id is required for platform admin"
            )

        target_client_id = client_id

    else:

        target_client_id = current_user["client_id"]

    subscription = (
        db.query(Subscription)
        .filter(
            Subscription.client_id == target_client_id,
            Subscription.status == "ACTIVE"
        )
        .first()
    )

    total_users = (
        db.query(User)
        .filter(
            User.client_id == client_id
        )
        .count()
    )

    active_users = (
        db.query(User)
        .filter(
            User.client_id == client_id,
            User.is_active == True
        )
        .count()
    )

    total_departments = (
        db.query(Department)
        .filter(
            Department.client_id == client_id,
            Department.is_active == True
        )
        .count()
    )

    total_assets = (
        db.query(Asset)
        .filter(
            Asset.client_id == client_id,
            Asset.is_active == True
        )
        .count()
    )

    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_departments": total_departments,
        "total_assets": total_assets,
        "subscription": {
            "max_assets": subscription.max_assets,
            "max_departments": subscription.max_departments,
            "licence_count": subscription.licence_count,
            "used_licences": subscription.used_licences
        }
    }