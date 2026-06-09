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