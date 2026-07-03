from fastapi import Depends
from fastapi import HTTPException
from fastapi.security import HTTPBearer
from app.config.dependencies import get_current_user
from jose import jwt

from app.config.settings import settings


security = HTTPBearer()


def get_current_admin(
    token=Depends(security)
):
    try:
        payload = jwt.decode(
            token.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        return payload

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )
def admin_required(
    current_admin=Depends(
        get_current_admin
    )
):
    if current_admin["role"] != "ADMIN":

        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return current_admin



def client_admin_required(
    current_user=Depends(
        get_current_user
    )
):

    if current_user["role"] != "CLIENT_ADMIN":

        raise HTTPException(
            status_code=403,
            detail="Client Admin access required"
        )

    return current_user



from app.config.dependencies import (
    get_current_user
)


def department_creator_required(
    current_user=Depends(
        get_current_user
    )
):

    allowed_roles = [
        "CLIENT_ADMIN",
        "MANAGER"
    ]

    if current_user["role"] not in allowed_roles:

        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions"
        )

    return current_user




def department_update_required(
    current_user=Depends(
        get_current_user
    )
):

    allowed_roles = [
        "ADMIN",
        "CLIENT_ADMIN",
        "MANAGER"
    ]

    if current_user["role"] not in allowed_roles:

        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions"
        )

    return current_user


def department_view_required(
    current_user=Depends(
        get_current_user
    )
):

    allowed_roles = [
        "ADMIN",
        "CLIENT_ADMIN",
        "MANAGER"
    ]

    if current_user["role"] not in allowed_roles:

        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions"
        )

    return current_user


def department_restore_required(
    current_user=Depends(
        get_current_user
    )
):

    allowed_roles = [
        "ADMIN",
        "CLIENT_ADMIN"
    ]

    if current_user["role"] not in allowed_roles:

        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions"
        )

    return current_user


def manager_create_required(
    current_user=Depends(
        get_current_user
    )
):

    allowed_roles = [
        "ADMIN",
        "CLIENT_ADMIN"
    ]

    if current_user["role"] not in allowed_roles:

        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions"
        )

    return current_user


def manager_create_required(
    current_user=Depends(
        get_current_user
    )
):

    allowed_roles = [
        "ADMIN",
        "CLIENT_ADMIN"
    ]

    if current_user["role"] not in allowed_roles:

        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions"
        )

    return current_user


def manager_view_required(
    current_user=Depends(
        get_current_user
    )
):

    allowed_roles = [
        "ADMIN",
        "CLIENT_ADMIN"
    ]

    if current_user["role"] not in allowed_roles:

        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions"
        )

    return current_user


from fastapi import Depends, HTTPException

from app.config.dependencies import get_current_user


def admin_only(
    current_user=Depends(get_current_user)
):
    """
    Allows access to:
    - Platform Admin (ADMIN)
    - Client Admin (CLIENT_ADMIN)
    """

    if current_user["role"] not in {"ADMIN", "CLIENT_ADMIN"}:
        raise HTTPException(
            status_code=403,
            detail="Only Platform Admin or Client Admin can access this resource."
        )

    return current_user



def manager_view_required(
    current_user=Depends(
        get_current_user
    )
):

    allowed_roles = [
        "ADMIN",
        "CLIENT_ADMIN"
    ]

    if current_user["role"] not in allowed_roles:

        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions"
        )

    return current_user




from fastapi import Depends
from fastapi import HTTPException

from app.config.dependencies import (
    get_current_user,
    get_db
)

'''

from app.utils.permissions import (
    has_permission
)


def service_permission_required(
    service_code: str,
    action: str
):

    def permission_checker(

        db=Depends(get_db),

        current_user=Depends(
            get_current_user
        )
    ):

        allowed = has_permission(
            db=db,
            user=current_user,
            service_code=service_code,
            action=action
        )

        if not allowed:

            raise HTTPException(
                status_code=403,
                detail=(
                    f"{action} permission "
                    f"required for "
                    f"{service_code}"
                )
            )

        return current_user

    return permission_checker


    '''


from fastapi import Depends
from fastapi import HTTPException

from app.config.dependencies import (
    get_current_user,
    get_db
)

from app.config.permission import (
    has_permission
)
def service_permission_required(
    service_code: str,
    action: str
):

    def permission_checker(

        db=Depends(get_db),

        current_user=Depends(
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
                detail=(
                    f"Permission denied. "
                    f"Required: "
                    f"{service_code}.{action}"
                )
            )

        return current_user

    return permission_checker