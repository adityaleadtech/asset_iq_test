from fastapi import HTTPException

from app.models.users import User
from app.models.roles import Role
from app.models.service_catalogue import ServiceCatalogue
from app.models.role_service_permissions import (
    RoleServicePermission
)


def has_permission(
    db,
    current_user,
    service_code: str,
    action: str
):

    if current_user["role"] == "ADMIN":

        return True

    if current_user["role"] == "CLIENT_ADMIN":

        return True

    user = (
        db.query(User)
        .filter(
            User.id ==
            current_user["user_id"],

            User.is_active == True
        )
        .first()
    )

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if not user.custom_role_id:

        raise HTTPException(
            status_code=403,
            detail="No role assigned"
        )

    service = (
        db.query(ServiceCatalogue)
        .filter(
            ServiceCatalogue.code
            ==
            service_code,

            ServiceCatalogue.is_active
            ==
            True
        )
        .first()
    )

    if not service:

        raise HTTPException(
            status_code=404,
            detail="Service not found"
        )

    permission = (
        db.query(
            RoleServicePermission
        )
        .filter(
            RoleServicePermission.role_id
            ==
            user.custom_role_id,

            RoleServicePermission.service_id
            ==
            service.id
        )
        .first()
    )

    if not permission:

        return False

    action = action.upper()

    if action == "CREATE":

        return permission.can_create

    if action == "READ":

        return permission.can_read

    if action == "UPDATE":

        return permission.can_update

    if action == "DELETE":

        return permission.can_delete

    return False
