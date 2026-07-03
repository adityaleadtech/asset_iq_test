from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.platform_admin import PlatformAdmin
from app.models.users import User

from app.schemas.login import (
    LoginRequest,
    LoginResponse,
    LoggedInUser
)

from app.utils.security import (
    verify_password,
)
from app.utils.jwthandler import (
    create_token
)


def authenticate_platform_admin(
    db: Session,
    payload: LoginRequest
):

    admin = (
        db.query(PlatformAdmin)
        .filter(
            PlatformAdmin.email == payload.email,
            PlatformAdmin.is_active == True
        )
        .first()
    )

    if not admin:
        return None

    if not verify_password(
        payload.password,
        admin.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password."
        )

    return admin


def authenticate_user(
    db: Session,
    payload: LoginRequest
):

    user = (
        db.query(User)
        .filter(
            User.email == payload.email,
            User.is_active == True
        )
        .first()
    )

    if not user:
        return None

    if not verify_password(
        payload.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password."
        )

    return user



def build_platform_admin_response(
    admin: PlatformAdmin
):

    token = create_token(
        {
            "id": admin.id,
            "role": "ADMIN"
        }
    )

    return LoginResponse(
        access_token=token,
        user=LoggedInUser(
            id=admin.id,
            name=admin.full_name,
            email=admin.email,
            role="ADMIN"
        )
    )


def build_user_response(
    user: User
):

    token = create_token(
        {
            "id": user.id,
            "client_id": user.client_id,
            "department_id": user.department_id,
            "custom_role_id": user.custom_role_id,
            "role": user.role
        }
    )

    return LoginResponse(
        access_token=token,
        user=LoggedInUser(
            id=user.id,
            name=user.full_name,
            email=user.email,
            role=user.role,
            client_id=user.client_id,
            department_id=user.department_id,
            custom_role_id=user.custom_role_id
        )
    )


def login(
    db: Session,
    payload: LoginRequest
):

    #
    # Platform Admin Login
    #
    admin = authenticate_platform_admin(
        db,
        payload
    )

    if admin:

        return build_platform_admin_response(
            admin
        )

    #
    # User Login
    #
    user = authenticate_user(
        db,
        payload
    )

    if user:

        return build_user_response(
            user
        )

    #
    # Invalid Credentials
    #
    raise HTTPException(
        status_code=401,
        detail="Invalid email or password."
    )