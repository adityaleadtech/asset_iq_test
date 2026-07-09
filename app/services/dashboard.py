from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.clients import Client
from app.models.departments import Department
from app.models.subscription import Subscription
from app.models.users import User


# ============================================================
# DASHBOARD ENTRY POINT
# ============================================================


def get_dashboard(
    db: Session,
    current_user: Dict[str, Any],
    client_id: Optional[str] = None,
    department_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Unified AssetIQ dashboard service.

    Access levels:

    PLATFORM_ADMIN / ADMIN
        - Platform dashboard
        - Any client dashboard
        - Any department dashboard
        - Any user dashboard

    CLIENT_ADMIN
        - Own client dashboard
        - Own client departments
        - Own client users

    MANAGER
        - Own assigned department dashboard

    USER
        - Own personal dashboard
    """

    user_role = current_user.get("role")
    current_user_id = current_user.get("id")
    current_user_client_id = current_user.get("client_id")
    current_user_department_id = current_user.get("department_id")

    if not user_role:
        raise HTTPException(
            status_code=401,
            detail="User role missing from authentication token",
        )

    user_role = str(user_role).upper()

    # ========================================================
    # PLATFORM ADMIN
    # ========================================================

    if user_role in ["PLATFORM_ADMIN", "ADMIN"]:

        if user_id:
            return _get_user_dashboard(
                db=db,
                user_id=user_id,
                client_id=client_id,
                department_id=department_id,
            )

        if department_id:
            return _get_department_dashboard(
                db=db,
                department_id=department_id,
                client_id=client_id,
            )

        if client_id:
            return _get_client_dashboard(
                db=db,
                client_id=client_id,
            )

        return _get_platform_dashboard(db=db)

    # ========================================================
    # CLIENT ADMIN
    # ========================================================

    if user_role == "CLIENT_ADMIN":

        if not current_user_client_id:
            raise HTTPException(
                status_code=400,
                detail="Client admin is not associated with any client",
            )

        if client_id and client_id != current_user_client_id:
            raise HTTPException(
                status_code=403,
                detail="Client admin cannot access another client's dashboard",
            )

        target_client_id = current_user_client_id

        # ----------------------------------------------------
        # USER DASHBOARD
        # ----------------------------------------------------

        if user_id:

            user = (
                db.query(User)
                .filter(
                    User.id == user_id,
                    User.client_id == target_client_id,
                    User.is_active == True,
                )
                .first()
            )

            if not user:
                raise HTTPException(
                    status_code=404,
                    detail="User not found in your client",
                )

            return _get_user_dashboard(
                db=db,
                user_id=user_id,
                client_id=target_client_id,
                department_id=department_id,
            )

        # ----------------------------------------------------
        # DEPARTMENT DASHBOARD
        # ----------------------------------------------------

        if department_id:

            department = (
                db.query(Department)
                .filter(
                    Department.id == department_id,
                    Department.client_id == target_client_id,
                    Department.is_active == True,
                )
                .first()
            )

            if not department:
                raise HTTPException(
                    status_code=404,
                    detail="Department not found in your client",
                )

            return _get_department_dashboard(
                db=db,
                department_id=department_id,
                client_id=target_client_id,
            )

        # ----------------------------------------------------
        # CLIENT DASHBOARD
        # ----------------------------------------------------

        return _get_client_dashboard(
            db=db,
            client_id=target_client_id,
        )

    # ========================================================
    # MANAGER
    # ========================================================

    if user_role == "MANAGER":

        if not current_user_department_id:
            raise HTTPException(
                status_code=400,
                detail="Manager is not assigned to any department",
            )

        if (
            department_id
            and department_id != current_user_department_id
        ):
            raise HTTPException(
                status_code=403,
                detail="Manager can only access their assigned department",
            )

        if (
            client_id
            and client_id != current_user_client_id
        ):
            raise HTTPException(
                status_code=403,
                detail="Manager cannot access another client",
            )

        if user_id:
            raise HTTPException(
                status_code=403,
                detail="Manager cannot access individual user dashboards",
            )

        department = (
            db.query(Department)
            .filter(
                Department.id == current_user_department_id,
                Department.client_id == current_user_client_id,
                Department.manager_id == current_user_id,
                Department.is_active == True,
            )
            .first()
        )

        if not department:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Assigned department not found "
                    "or manager assignment is invalid"
                ),
            )

        return _get_department_dashboard(
            db=db,
            department_id=current_user_department_id,
            client_id=current_user_client_id,
        )

    # ========================================================
    # USER
    # ========================================================

    if user_role == "USER":

        if user_id and user_id != current_user_id:
            raise HTTPException(
                status_code=403,
                detail="User can only access their own dashboard",
            )

        if (
            client_id
            and client_id != current_user_client_id
        ):
            raise HTTPException(
                status_code=403,
                detail="User cannot access another client",
            )

        if (
            department_id
            and department_id != current_user_department_id
        ):
            raise HTTPException(
                status_code=403,
                detail="User cannot access another department",
            )

        return _get_user_dashboard(
            db=db,
            user_id=current_user_id,
            client_id=current_user_client_id,
            department_id=current_user_department_id,
        )

    raise HTTPException(
        status_code=403,
        detail=f"Dashboard access is not supported for role '{user_role}'",
    )


# ============================================================
# PLATFORM DASHBOARD
# ============================================================


def _get_platform_dashboard(
    db: Session,
) -> Dict[str, Any]:
    """
    Platform administrator dashboard.

    Provides complete AssetIQ platform overview.
    """

    # ========================================================
    # CLIENT STATISTICS
    # ========================================================

    total_clients = db.query(Client).count()

    active_clients = (
        db.query(Client)
        .filter(Client.is_active == True)
        .count()
    )

    inactive_clients = (
        db.query(Client)
        .filter(Client.is_active == False)
        .count()
    )

    # ========================================================
    # SUBSCRIPTION STATISTICS
    # ========================================================

    total_subscriptions = db.query(Subscription).count()

    active_subscriptions = (
        db.query(Subscription)
        .filter(Subscription.status == "ACTIVE")
        .count()
    )

    expired_subscriptions = (
        db.query(Subscription)
        .filter(
            Subscription.ends_at.isnot(None),
            Subscription.ends_at < datetime.utcnow(),
        )
        .count()
    )

    # ========================================================
    # USER STATISTICS
    # ========================================================

    total_users = (
        db.query(User)
        .filter(User.is_active == True)
        .count()
    )

    total_client_admins = (
        db.query(User)
        .filter(
            User.role == "CLIENT_ADMIN",
            User.is_active == True,
        )
        .count()
    )

    total_managers = (
        db.query(User)
        .filter(
            User.role == "MANAGER",
            User.is_active == True,
        )
        .count()
    )

    total_normal_users = (
        db.query(User)
        .filter(
            User.role == "USER",
            User.is_active == True,
        )
        .count()
    )

    # ========================================================
    # DEPARTMENT STATISTICS
    # ========================================================

    total_departments = (
        db.query(Department)
        .filter(Department.is_active == True)
        .count()
    )

    # ========================================================
    # ASSET STATISTICS
    # ========================================================

    total_assets = (
        db.query(Asset)
        .filter(Asset.is_active == True)
        .count()
    )

    assigned_assets = (
        db.query(Asset)
        .filter(
            Asset.assigned_to_user_id.isnot(None),
            Asset.is_active == True,
        )
        .count()
    )

    unassigned_assets = (
        db.query(Asset)
        .filter(
            Asset.assigned_to_user_id.is_(None),
            Asset.is_active == True,
        )
        .count()
    )

    tagged_assets = (
        db.query(Asset)
        .filter(
            Asset.tag_state == "TAGGED",
            Asset.is_active == True,
        )
        .count()
    )

    not_tagged_assets = (
        db.query(Asset)
        .filter(
            Asset.tag_state == "NOT_TAGGED",
            Asset.is_active == True,
        )
        .count()
    )

    damaged_assets = (
        db.query(Asset)
        .filter(
            Asset.asset_condition == "DAMAGED",
            Asset.is_active == True,
        )
        .count()
    )

    maintenance_assets = (
        db.query(Asset)
        .filter(
            Asset.asset_condition == "UNDER_MAINTENANCE",
            Asset.is_active == True,
        )
        .count()
    )

    lost_assets = (
        db.query(Asset)
        .filter(
            Asset.asset_condition == "LOST",
            Asset.is_active == True,
        )
        .count()
    )

    inactive_assets = (
        db.query(Asset)
        .filter(
            Asset.asset_condition == "INACTIVE",
            Asset.is_active == True,
        )
        .count()
    )

    # ========================================================
    # RECENT CLIENTS
    # ========================================================

    recent_clients = (
        db.query(Client)
        .order_by(Client.created_at.desc())
        .limit(5)
        .all()
    )

    # ========================================================
    # RECENT SUBSCRIPTIONS
    # ========================================================

    recent_subscriptions = (
        db.query(Subscription)
        .order_by(Subscription.created_at.desc())
        .limit(5)
        .all()
    )

    return {
        "level": "platform",

        "summary": {
            "clients": {
                "total": total_clients,
                "active": active_clients,
                "inactive": inactive_clients,
            },

            "subscriptions": {
                "total": total_subscriptions,
                "active": active_subscriptions,
                "expired": expired_subscriptions,
            },

            "users": {
                "total": total_users,
                "client_admins": total_client_admins,
                "managers": total_managers,
                "users": total_normal_users,
            },

            "departments": {
                "total": total_departments,
            },

            "assets": {
                "total": total_assets,
                "assigned": assigned_assets,
                "unassigned": unassigned_assets,

                "tagged": tagged_assets,
                "not_tagged": not_tagged_assets,

                "active": (
                    db.query(Asset)
                    .filter(
                        Asset.asset_condition == "ACTIVE",
                        Asset.is_active == True,
                    )
                    .count()
                ),

                "inactive": inactive_assets,
                "damaged": damaged_assets,
                "under_maintenance": maintenance_assets,
                "lost": lost_assets,
            },
        },

        "recent_clients": [
            {
                "id": client.id,
                "name": client.name,
                "client_code": getattr(
                    client,
                    "client_code",
                    None,
                ),
                "is_active": client.is_active,
                "created_at": getattr(
                    client,
                    "created_at",
                    None,
                ),
            }
            for client in recent_clients
        ],

        "recent_subscriptions": [
            {
                "id": subscription.id,
                "client_id": subscription.client_id,
                "status": subscription.status,
                "licence_count": subscription.licence_count,
                "used_licences": subscription.used_licences,
                "max_assets": subscription.max_assets,
                "max_departments": subscription.max_departments,
                "price": subscription.price,
                "starts_at": subscription.starts_at,
                "ends_at": subscription.ends_at,
                "auto_renew": subscription.auto_renew,
                "created_at": subscription.created_at,
            }
            for subscription in recent_subscriptions
        ],
    }


# ============================================================
# CLIENT DASHBOARD
# ============================================================


def _get_client_dashboard(
    db: Session,
    client_id: str,
) -> Dict[str, Any]:
    """
    Client administrator dashboard.

    Provides:
    - Client information
    - Subscription details
    - Licence utilization
    - User statistics
    - Department statistics
    - Asset statistics
    - Department breakdown
    - Recent users
    - Recent assets
    """

    client = (
        db.query(Client)
        .filter(Client.id == client_id)
        .first()
    )

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Client not found",
        )

    # ========================================================
    # ACTIVE SUBSCRIPTION
    # ========================================================

    subscription = (
        db.query(Subscription)
        .filter(
            Subscription.client_id == client_id,
            Subscription.status == "ACTIVE",
        )
        .order_by(Subscription.created_at.desc())
        .first()
    )

    # ========================================================
    # USER STATISTICS
    # ========================================================

    total_users = (
        db.query(User)
        .filter(
            User.client_id == client_id,
            User.is_active == True,
        )
        .count()
    )

    total_client_admins = (
        db.query(User)
        .filter(
            User.client_id == client_id,
            User.role == "CLIENT_ADMIN",
            User.is_active == True,
        )
        .count()
    )

    total_managers = (
        db.query(User)
        .filter(
            User.client_id == client_id,
            User.role == "MANAGER",
            User.is_active == True,
        )
        .count()
    )

    total_normal_users = (
        db.query(User)
        .filter(
            User.client_id == client_id,
            User.role == "USER",
            User.is_active == True,
        )
        .count()
    )

    # ========================================================
    # DEPARTMENTS
    # ========================================================

    departments = (
        db.query(Department)
        .filter(
            Department.client_id == client_id,
            Department.is_active == True,
        )
        .order_by(Department.created_at.desc())
        .all()
    )

    total_departments = len(departments)

    # ========================================================
    # ASSET STATISTICS
    # ========================================================

    asset_query = (
        db.query(Asset)
        .filter(
            Asset.client_id == client_id,
            Asset.is_active == True,
        )
    )

    total_assets = asset_query.count()

    assigned_assets = asset_query.filter(
        Asset.assigned_to_user_id.isnot(None)
    ).count()

    unassigned_assets = asset_query.filter(
        Asset.assigned_to_user_id.is_(None)
    ).count()

    tagged_assets = asset_query.filter(
        Asset.tag_state == "TAGGED"
    ).count()

    not_tagged_assets = asset_query.filter(
        Asset.tag_state == "NOT_TAGGED"
    ).count()

    active_assets = asset_query.filter(
        Asset.asset_condition == "ACTIVE"
    ).count()

    inactive_assets = asset_query.filter(
        Asset.asset_condition == "INACTIVE"
    ).count()

    damaged_assets = asset_query.filter(
        Asset.asset_condition == "DAMAGED"
    ).count()

    maintenance_assets = asset_query.filter(
        Asset.asset_condition == "UNDER_MAINTENANCE"
    ).count()

    lost_assets = asset_query.filter(
        Asset.asset_condition == "LOST"
    ).count()

    # ========================================================
    # RECENT USERS
    # ========================================================

    recent_users = (
        db.query(User)
        .filter(
            User.client_id == client_id,
            User.is_active == True,
        )
        .order_by(User.created_at.desc())
        .limit(5)
        .all()
    )

    # ========================================================
    # RECENT ASSETS
    # ========================================================

    recent_assets = (
        db.query(Asset)
        .filter(
            Asset.client_id == client_id,
            Asset.is_active == True,
        )
        .order_by(Asset.created_at.desc())
        .limit(10)
        .all()
    )

    # ========================================================
    # SUBSCRIPTION SUMMARY
    # ========================================================

    subscription_summary = None

    if subscription:

        licence_count = subscription.licence_count or 0
        used_licences = subscription.used_licences or 0

        available_licences = max(
            licence_count - used_licences,
            0,
        )

        usage_percentage = 0

        if licence_count > 0:
            usage_percentage = round(
                (used_licences / licence_count) * 100,
                2,
            )

        subscription_summary = {
            "id": subscription.id,
            "status": subscription.status,

            "licence_count": licence_count,
            "used_licences": used_licences,
            "available_licences": available_licences,
            "usage_percentage": usage_percentage,

            "max_assets": subscription.max_assets,
            "max_departments": subscription.max_departments,
            "price": subscription.price,

            "starts_at": subscription.starts_at,
            "ends_at": subscription.ends_at,
            "auto_renew": subscription.auto_renew,
            "created_at": subscription.created_at,
        }

    # ========================================================
    # DEPARTMENT DETAILS
    # ========================================================

    department_details = []

    for department in departments:

        department_users = (
            db.query(User)
            .filter(
                User.department_id == department.id,
                User.client_id == client_id,
                User.is_active == True,
            )
            .count()
        )

        department_assets = (
            db.query(Asset)
            .filter(
                Asset.department_id == department.id,
                Asset.client_id == client_id,
                Asset.is_active == True,
            )
            .count()
        )

        manager = None

        if department.manager_id:

            manager = (
                db.query(User)
                .filter(
                    User.id == department.manager_id,
                    User.client_id == client_id,
                    User.is_active == True,
                )
                .first()
            )

        department_details.append(
            {
                "id": department.id,
                "name": department.name,
                "code": getattr(
                    department,
                    "code",
                    None,
                ),

                "manager": {
                    "id": manager.id,
                    "full_name": manager.full_name,
                    "email": manager.email,
                }
                if manager
                else None,

                "total_users": department_users,
                "total_assets": department_assets,
                "is_active": department.is_active,
            }
        )

    return {
        "level": "client",

        "client": {
            "id": client.id,
            "name": client.name,
            "client_code": getattr(
                client,
                "client_code",
                None,
            ),
            "is_active": client.is_active,
            "created_at": getattr(
                client,
                "created_at",
                None,
            ),
        },

        "summary": {
            "users": {
                "total": total_users,
                "client_admins": total_client_admins,
                "managers": total_managers,
                "users": total_normal_users,
            },

            "departments": {
                "total": total_departments,
            },

            "assets": {
                "total": total_assets,

                "assigned": assigned_assets,
                "unassigned": unassigned_assets,

                "tagged": tagged_assets,
                "not_tagged": not_tagged_assets,

                "active": active_assets,
                "inactive": inactive_assets,
                "damaged": damaged_assets,
                "under_maintenance": maintenance_assets,
                "lost": lost_assets,
            },
        },

        "subscription": subscription_summary,

        "departments": department_details,

        "recent_users": [
            {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "role": user.role,
                "department_id": user.department_id,
                "created_at": getattr(
                    user,
                    "created_at",
                    None,
                ),
            }
            for user in recent_users
        ],

        "recent_assets": [
            {
                "id": asset.id,
                "name": asset.name,
                "serial_number": asset.serial_number,
                "model": asset.model,
                "manufacturer": asset.manufacturer,

                "department_id": asset.department_id,
                "location_id": asset.location_id,

                "assigned_to_user_id": (
                    asset.assigned_to_user_id
                ),

                "asset_condition": asset.asset_condition,
                "tag_state": asset.tag_state,

                "current_latitude": asset.current_latitude,
                "current_longitude": asset.current_longitude,

                "latest_image_url": asset.latest_image_url,

                "created_at": asset.created_at,
            }
            for asset in recent_assets
        ],
    }


# ============================================================
# DEPARTMENT DASHBOARD
# ============================================================


def _get_department_dashboard(
    db: Session,
    department_id: str,
    client_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Department dashboard.

    Provides:
    - Department details
    - Manager
    - Team information
    - Asset statistics
    - Asset conditions
    - Tagging statistics
    - Recent assets
    """

    department = (
        db.query(Department)
        .filter(
            Department.id == department_id,
            Department.is_active == True,
        )
        .first()
    )

    if not department:
        raise HTTPException(
            status_code=404,
            detail="Department not found",
        )

    if (
        client_id
        and department.client_id != client_id
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "Department does not belong "
                "to the specified client"
            ),
        )

    # ========================================================
    # MANAGER
    # ========================================================

    manager = None

    if department.manager_id:

        manager = (
            db.query(User)
            .filter(
                User.id == department.manager_id,
                User.is_active == True,
            )
            .first()
        )

    # ========================================================
    # TEAM MEMBERS
    # ========================================================

    team_members = (
        db.query(User)
        .filter(
            User.department_id == department_id,
            User.is_active == True,
        )
        .order_by(User.created_at.desc())
        .all()
    )

    total_team_members = len(team_members)

    managers = sum(
        1
        for user in team_members
        if str(user.role).upper() == "MANAGER"
    )

    normal_users = sum(
        1
        for user in team_members
        if str(user.role).upper() == "USER"
    )

    # ========================================================
    # ASSET STATISTICS
    # ========================================================

    asset_query = (
        db.query(Asset)
        .filter(
            Asset.department_id == department_id,
            Asset.is_active == True,
        )
    )

    total_assets = asset_query.count()

    assigned_assets = asset_query.filter(
        Asset.assigned_to_user_id.isnot(None)
    ).count()

    unassigned_assets = asset_query.filter(
        Asset.assigned_to_user_id.is_(None)
    ).count()

    tagged_assets = asset_query.filter(
        Asset.tag_state == "TAGGED"
    ).count()

    not_tagged_assets = asset_query.filter(
        Asset.tag_state == "NOT_TAGGED"
    ).count()

    active_assets = asset_query.filter(
        Asset.asset_condition == "ACTIVE"
    ).count()

    inactive_assets = asset_query.filter(
        Asset.asset_condition == "INACTIVE"
    ).count()

    damaged_assets = asset_query.filter(
        Asset.asset_condition == "DAMAGED"
    ).count()

    maintenance_assets = asset_query.filter(
        Asset.asset_condition == "UNDER_MAINTENANCE"
    ).count()

    lost_assets = asset_query.filter(
        Asset.asset_condition == "LOST"
    ).count()

    # ========================================================
    # RECENT ASSETS
    # ========================================================

    recent_assets = (
        asset_query
        .order_by(Asset.created_at.desc())
        .limit(10)
        .all()
    )

    return {
        "level": "department",

        "department": {
            "id": department.id,
            "name": department.name,
            "code": getattr(
                department,
                "code",
                None,
            ),
            "client_id": department.client_id,
            "location_id": getattr(
                department,
                "location_id",
                None,
            ),
            "is_active": department.is_active,
        },

        "manager": {
            "id": manager.id,
            "full_name": manager.full_name,
            "email": manager.email,
        }
        if manager
        else None,

        "summary": {
            "team": {
                "total_members": total_team_members,
                "managers": managers,
                "users": normal_users,
            },

            "assets": {
                "total": total_assets,

                "assigned": assigned_assets,
                "unassigned": unassigned_assets,

                "tagged": tagged_assets,
                "not_tagged": not_tagged_assets,

                "active": active_assets,
                "inactive": inactive_assets,
                "damaged": damaged_assets,
                "under_maintenance": maintenance_assets,
                "lost": lost_assets,
            },
        },

        "team_members": [
            {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "role": user.role,
                "employee_id": getattr(
                    user,
                    "employee_id",
                    None,
                ),
                "profile_photo_url": getattr(
                    user,
                    "profile_photo_url",
                    None,
                ),
                "created_at": user.created_at,
            }
            for user in team_members
        ],

        "recent_assets": [
            {
                "id": asset.id,
                "name": asset.name,
                "serial_number": asset.serial_number,
                "model": asset.model,
                "manufacturer": asset.manufacturer,

                "assigned_to_user_id": (
                    asset.assigned_to_user_id
                ),

                "asset_condition": asset.asset_condition,
                "tag_state": asset.tag_state,

                "location_id": asset.location_id,

                "current_latitude": asset.current_latitude,
                "current_longitude": asset.current_longitude,

                "latest_image_url": asset.latest_image_url,

                "last_scanned_at": asset.last_scanned_at,
                "created_at": asset.created_at,
            }
            for asset in recent_assets
        ],
    }


# ============================================================
# USER DASHBOARD
# ============================================================


def _get_user_dashboard(
    db: Session,
    user_id: str,
    client_id: Optional[str] = None,
    department_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    User dashboard.

    Provides:
    - User profile
    - Department
    - Department manager
    - Assigned asset statistics
    - Asset condition breakdown
    - Tagging information
    - Assigned assets
    """

    user = (
        db.query(User)
        .filter(
            User.id == user_id,
            User.is_active == True,
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    if (
        client_id
        and user.client_id != client_id
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "User does not belong "
                "to the specified client"
            ),
        )

    if (
        department_id
        and user.department_id != department_id
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "User does not belong "
                "to the specified department"
            ),
        )

    # ========================================================
    # DEPARTMENT
    # ========================================================

    department = None
    manager = None

    if user.department_id:

        department = (
            db.query(Department)
            .filter(
                Department.id == user.department_id,
                Department.is_active == True,
            )
            .first()
        )

        if department and department.manager_id:

            manager = (
                db.query(User)
                .filter(
                    User.id == department.manager_id,
                    User.is_active == True,
                )
                .first()
            )

    # ========================================================
    # ASSIGNED ASSETS
    # ========================================================

    asset_query = (
        db.query(Asset)
        .filter(
            Asset.assigned_to_user_id == user_id,
            Asset.is_active == True,
        )
    )

    assigned_assets = (
        asset_query
        .order_by(Asset.created_at.desc())
        .all()
    )

    total_assets = len(assigned_assets)

    active_assets = sum(
        1
        for asset in assigned_assets
        if asset.asset_condition == "ACTIVE"
    )

    inactive_assets = sum(
        1
        for asset in assigned_assets
        if asset.asset_condition == "INACTIVE"
    )

    damaged_assets = sum(
        1
        for asset in assigned_assets
        if asset.asset_condition == "DAMAGED"
    )

    maintenance_assets = sum(
        1
        for asset in assigned_assets
        if asset.asset_condition == "UNDER_MAINTENANCE"
    )

    lost_assets = sum(
        1
        for asset in assigned_assets
        if asset.asset_condition == "LOST"
    )

    tagged_assets = sum(
        1
        for asset in assigned_assets
        if asset.tag_state == "TAGGED"
    )

    not_tagged_assets = sum(
        1
        for asset in assigned_assets
        if asset.tag_state == "NOT_TAGGED"
    )

    return {
        "level": "user",

        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "phone": getattr(
                user,
                "phone",
                None,
            ),
            "employee_id": getattr(
                user,
                "employee_id",
                None,
            ),
            "profile_photo_url": getattr(
                user,
                "profile_photo_url",
                None,
            ),
            "role": user.role,
            "client_id": user.client_id,
            "department_id": user.department_id,
            "is_active": user.is_active,
        },

        "department": {
            "id": department.id,
            "name": department.name,
            "code": getattr(
                department,
                "code",
                None,
            ),
        }
        if department
        else None,

        "manager": {
            "id": manager.id,
            "full_name": manager.full_name,
            "email": manager.email,
        }
        if manager
        else None,

        "summary": {
            "assets": {
                "total": total_assets,

                "tagged": tagged_assets,
                "not_tagged": not_tagged_assets,

                "active": active_assets,
                "inactive": inactive_assets,
                "damaged": damaged_assets,
                "under_maintenance": maintenance_assets,
                "lost": lost_assets,
            },
        },

        "assigned_assets": [
            {
                "id": asset.id,
                "name": asset.name,
                "description": asset.description,

                "serial_number": asset.serial_number,
                "model": asset.model,
                "manufacturer": asset.manufacturer,

                "purchase_date": asset.purchase_date,
                "purchase_value": asset.purchase_value,

                "asset_condition": asset.asset_condition,
                "tag_state": asset.tag_state,

                "category_id": asset.category_id,
                "type_id": asset.type_id,
                "parent_asset_id": asset.parent_asset_id,

                "department_id": asset.department_id,
                "location_id": asset.location_id,

                "assigned_to_user_id": (
                    asset.assigned_to_user_id
                ),

                "current_latitude": asset.current_latitude,
                "current_longitude": asset.current_longitude,

                "last_scanned_by": asset.last_scanned_by,
                "last_scanned_at": asset.last_scanned_at,

                "qr_code_url": asset.qr_code_url,
                "created_image_url": asset.created_image_url,
                "latest_image_url": asset.latest_image_url,

                "remarks": asset.remarks,
                "metadata_json": asset.metadata_json,
                "custom_fields": asset.custom_fields,

                "created_at": asset.created_at,
                "updated_at": asset.updated_at,
            }
            for asset in assigned_assets
        ],
    }