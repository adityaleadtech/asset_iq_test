from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any

from app.models.users import User
from app.models.departments import Department
from app.models.asset import Asset
from app.models.subscription import Subscription
from app.schemas.dashboard import (
    ClientDashboardResponse,
    SubscriptionSummary,
    AdminDashboardResponse
)

from datetime import datetime

from app.models.clients import Client
from app.models.subscription import Subscription
from app.models.users import User
from app.models.asset import Asset


def get_client_dashboard(
    db: Session,
    current_user: Dict[str, Any],
    client_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get dashboard data for a client.
    - ADMIN can specify client_id
    - Others use their own client_id
    """
    
    # ADMIN can view any client's dashboard
    if current_user["role"] == "ADMIN":
        if not client_id:
            raise HTTPException(
                status_code=400,
                detail="client_id is required for platform admin"
            )
        target_client_id = client_id
    else:
        target_client_id = current_user["client_id"]

    # Get subscription
    subscription = (
        db.query(Subscription)
        .filter(
            Subscription.client_id == target_client_id,
            Subscription.status == "ACTIVE"
        )
        .first()
    )

    # Calculate all metrics
    total_users = (
        db.query(User)
        .filter(
            User.client_id == target_client_id,
            User.is_active == True
        )
        .count()
    )

    total_managers = (
        db.query(User)
        .filter(
            User.client_id == target_client_id,
            User.role == "MANAGER",
            User.is_active == True
        )
        .count()
    )

    total_departments = (
        db.query(Department)
        .filter(
            Department.client_id == target_client_id,
            Department.is_active == True
        )
        .count()
    )

    total_assets = (
        db.query(Asset)
        .filter(
            Asset.client_id == target_client_id,
            Asset.is_active == True
        )
        .count()
    )

    assigned_assets = (
        db.query(Asset)
        .filter(
            Asset.client_id == target_client_id,
            Asset.status == "ASSIGNED",
            Asset.is_active == True
        )
        .count()
    )

    available_assets = (
        db.query(Asset)
        .filter(
            Asset.client_id == target_client_id,
            Asset.status == "AVAILABLE",
            Asset.is_active == True
        )
        .count()
    )

    # Build subscription summary
    subscription_summary = None
    if subscription:
        subscription_summary = SubscriptionSummary(
            licence_count=subscription.licence_count,
            used_licences=subscription.used_licences,
            max_assets=subscription.max_assets,
            max_departments=subscription.max_departments,
            starts_at=subscription.starts_at,
            ends_at=subscription.ends_at,
            status=subscription.status
        )

    return {
        "total_users": total_users,
        "total_managers": total_managers,
        "total_departments": total_departments,
        "total_assets": total_assets,
        "assigned_assets": assigned_assets,
        "available_assets": available_assets,
        "subscription": subscription_summary
    }


def get_admin_dashboard(
    db: Session,
    current_user: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Get aggregated dashboard for all clients (ADMIN only).
    """
    if current_user["role"] != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Only platform admins can access this endpoint"
        )

    # Get all active clients with their subscriptions
    subscriptions = (
        db.query(Subscription)
        .filter(Subscription.status == "ACTIVE")
        .all()
    )

    total_users = db.query(User).filter(User.is_active == True).count()
    total_managers = db.query(User).filter(
        User.role == "MANAGER",
        User.is_active == True
    ).count()
    total_departments = db.query(Department).filter(
        Department.is_active == True
    ).count()
    total_assets = db.query(Asset).filter(Asset.is_active == True).count()
    assigned_assets = db.query(Asset).filter(
        Asset.status == "ASSIGNED",
        Asset.is_active == True
    ).count()
    available_assets = db.query(Asset).filter(
        Asset.status == "AVAILABLE",
        Asset.is_active == True
    ).count()

    return {
        "total_users": total_users,
        "total_managers": total_managers,
        "total_departments": total_departments,
        "total_assets": total_assets,
        "assigned_assets": assigned_assets,
        "available_assets": available_assets,
        "active_subscriptions": len(subscriptions)
    }

def get_platform_dashboard(
    db,
    current_admin
):

    total_clients = (
        db.query(Client)
        .count()
    )

    active_clients = (
        db.query(Client)
        .filter(
            Client.is_active == True
        )
        .count()
    )

    inactive_clients = (
        db.query(Client)
        .filter(
            Client.is_active == False
        )
        .count()
    )

    total_subscriptions = (
        db.query(Subscription)
        .count()
    )

    active_subscriptions = (
        db.query(Subscription)
        .filter(
            Subscription.status == "ACTIVE"
        )
        .count()
    )

    expired_subscriptions = (
        db.query(Subscription)
        .filter(
            Subscription.ends_at < datetime.utcnow()
        )
        .count()
    )

    total_users = (
        db.query(User)
        .filter(
            User.is_active == True
        )
        .count()
    )

    total_managers = (
        db.query(User)
        .filter(
            User.role == "MANAGER",
            User.is_active == True
        )
        .count()
    )

    total_assets = (
        db.query(Asset)
        .filter(
            Asset.is_active == True
        )
        .count()
    )

    assigned_assets = (
        db.query(Asset)
        .filter(
            Asset.status == "ASSIGNED",
            Asset.is_active == True
        )
        .count()
    )

    available_assets = (
        db.query(Asset)
        .filter(
            Asset.status == "AVAILABLE",
            Asset.is_active == True
        )
        .count()
    )

    return {
        "total_clients": total_clients,
        "active_clients": active_clients,
        "inactive_clients": inactive_clients,

        "total_subscriptions": total_subscriptions,
        "active_subscriptions": active_subscriptions,
        "expired_subscriptions": expired_subscriptions,

        "total_users": total_users,
        "total_managers": total_managers,

        "total_assets": total_assets,
        "assigned_assets": assigned_assets,
        "available_assets": available_assets
    }



from fastapi import HTTPException

from app.models.departments import Department
from app.models.users import User
from app.models.asset import Asset


def get_manager_dashboard(
    db,
    current_user
):
    if current_user["role"] != "MANAGER":
        raise HTTPException(
            status_code=403,
            detail="Manager access required"
        )

    department = (
        db.query(Department)
        .filter(
            Department.manager_id == current_user["id"],
            Department.is_active == True
        )
        .first()
    )

    if not department:
        raise HTTPException(
            status_code=404,
            detail="No department assigned"
        )

    total_team_members = (
        db.query(User)
        .filter(
            User.department_id == department.id,
            User.is_active == True
        )
        .count()
    )

    total_assets = (
        db.query(Asset)
        .filter(
            Asset.department_id == department.id,
            Asset.is_active == True
        )
        .count()
    )

    assigned_assets = (
        db.query(Asset)
        .filter(
            Asset.department_id == department.id,
            Asset.status == "ASSIGNED",
            Asset.is_active == True
        )
        .count()
    )

    available_assets = (
        db.query(Asset)
        .filter(
            Asset.department_id == department.id,
            Asset.status == "AVAILABLE",
            Asset.is_active == True
        )
        .count()
    )

    # To be implemented later
    maintenance_pending = 0
    geofence_alerts = 0

    return {
        "department": {
            "id": department.id,
            "name": department.name
        },
        "total_team_members": total_team_members,
        "total_assets": total_assets,
        "assigned_assets": assigned_assets,
        "available_assets": available_assets,
        "maintenance_pending": maintenance_pending,
        "geofence_alerts": geofence_alerts
    }