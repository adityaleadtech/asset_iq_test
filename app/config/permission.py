from sqlalchemy.orm import Session

from app.models.role_service_permissions import (
    RoleServicePermission
)
from app.models.service_catalogue import (
    ServiceCatalogue
)


def has_permission(
    db: Session,
    user: dict,
    service_code: str,
    action: str
) -> bool:
    """
    Permission Hierarchy

    1. ADMIN
       - Full system access

    2. CLIENT_ADMIN
       - Full access within their client

    3. MANAGER
       - Department access
       - Full asset management in their department
       - Read departments
       - Read/update users in their department

    4. Custom Roles
       - RoleServicePermission based access
    """

    # Platform Admin
    if user["role"] == "ADMIN":
        return True

    # Client Admin
    if user["role"] == "CLIENT_ADMIN":
        return True

    # Manager permissions
    if user["role"] == "MANAGER":

        manager_permissions = {
            "DEPARTMENTS": [
                "read"
            ],
            "USERS": [
                "read",
                "update"
            ],
            "ASSET_MANAGEMENT": [
                "create",
                "read",
                "update",
                "delete"
            ]
        }

        return (
            action
            in
            manager_permissions.get(
                service_code,
                []
            )
        )

    # Custom Role Permissions
    role_id = user.get(
        "custom_role_id"
    )

    if not role_id:
        return False

    permission = (
        db.query(
            RoleServicePermission
        )
        .join(
            ServiceCatalogue,
            RoleServicePermission.service_id
            ==
            ServiceCatalogue.id
        )
        .filter(
            RoleServicePermission.role_id
            ==
            role_id,

            ServiceCatalogue.code
            ==
            service_code
        )
        .first()
    )

    if not permission:
        return False

    action_map = {
        "create": permission.can_create,
        "read": permission.can_read,
        "update": permission.can_update,
        "delete": permission.can_delete
    }

    return action_map.get(
        action,
        False
    )