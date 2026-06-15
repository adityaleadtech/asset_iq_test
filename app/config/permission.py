from fastapi import Depends
from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.config.dependencies import (
    get_db,
    get_current_user
)

from app.services.permissions import (
    has_permission
)



def require_permission(
    service_code: str,
    action: str
):

    def permission_checker(

        db: Session = Depends(get_db),

        current_user=
        Depends(
            get_current_user
        )
    ):

        allowed = has_permission(
            db,
            current_user,
            service_code,
            action
        )

        if not allowed:

            raise HTTPException(
                status_code=403,
                detail=
                (
                    f"No permission "
                    f"to {action} "
                    f"{service_code}"
                )
            )

        return True

    return permission_checker



from app.models.role_service_permissions import (
    RoleServicePermission
)

from app.models.service_catalogue import (
    ServiceCatalogue
)


def has_permission(
    db,
    user,
    service_code: str,
    action: str
):

    # Platform Admin always allowed
    if user["role"] == "ADMIN":
        return True

    # Client Admin always allowed
    if user["role"] == "CLIENT_ADMIN":
        return True

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



