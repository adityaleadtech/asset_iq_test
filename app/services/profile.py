from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.users import User
from app.models.departments import Department
from app.models.subscription import Subscription
from app.models.subscription_service import SubscriptionService
from app.models.service_catalogue import ServiceCatalogue
from app.models.platform_admin import PlatformAdmin


def get_profile(
    db: Session,
    current_user: dict
):
    role = current_user["role"]
    user_id = current_user["id"]

    #
    # ========================================================
    # PLATFORM ADMIN PROFILE
    # ========================================================
    #

    if role == "ADMIN":
        admin = (
            db.query(PlatformAdmin)
            .filter(
                PlatformAdmin.id == user_id
            )
            .first()
        )

        if not admin:
            raise HTTPException(
                status_code=404,
                detail="Platform admin not found."
            )

        return {
            "id": admin.id,
            "full_name": admin.full_name,
            "department_name": None,
            "role": "ADMIN",
            "email": admin.email,
            "is_active": admin.is_active,
            "subscribed": True,
            "services": "Admin access to all services"
        }

    #
    # ========================================================
    # CLIENT USER PROFILE
    # ========================================================
    #

    user = (
        db.query(User)
        .filter(
            User.id == user_id
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found."
        )

    #
    # Get department
    #

    department_name = None

    if user.department_id:
        department = (
            db.query(Department)
            .filter(
                Department.id
                == user.department_id
            )
            .first()
        )

        if department:
            department_name = (
                department.name
            )

    #
    # Get active subscription
    #

    subscription = (
        db.query(Subscription)
        .filter(
            Subscription.client_id
            == user.client_id,
            Subscription.status == "ACTIVE"
        )
        .first()
    )

    subscribed = (
        subscription is not None
    )

    #
    # Get subscription services
    #

    services = []

    if subscription:
        service_results = (
            db.query(
                ServiceCatalogue.code
            )
            .join(
                SubscriptionService,
                SubscriptionService.service_id
                == ServiceCatalogue.id
            )
            .filter(
                SubscriptionService.subscription_id
                == subscription.id,
                ServiceCatalogue.is_active.is_(
                    True
                )
            )
            .all()
        )

        services = [
            service.code
            for service in service_results
        ]

    #
    # Return profile
    #

    return {
        "id": user.id,
        "full_name": user.full_name,
        "department_name": department_name,
        "role": user.role,
        "phone": user.phone,
        "email": user.email,
        "profile_photo_url": (
            user.profile_photo_url
        ),
        "is_active": user.is_active,
        "subscribed": subscribed,
        "services": services
    }