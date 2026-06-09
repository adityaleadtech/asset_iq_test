import uuid

from fastapi import HTTPException

from app.models.users import User
from app.utils.security import hash_password


def create_client_admin(
    db,
    admin_data
):
    existing_client_admin = (
        db.query(User)
        .filter(
            User.client_id == admin_data.client_id,
            User.role == "CLIENT_ADMIN"
        )
        .first()
    )

    if existing_client_admin:
        raise HTTPException(
            status_code=400,
            detail="Client Admin already exists for this client"
        )

    existing_email = (
        db.query(User)
        .filter(
            User.client_id == admin_data.client_id,
            User.email == admin_data.email
        )
        .first()
    )

    if existing_email:
        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )

    user = User(
        id=str(uuid.uuid4()),
        client_id=admin_data.client_id,
        email=admin_data.email,
        password_hash=hash_password(
            admin_data.password
        ),
        full_name=admin_data.full_name,
        phone=admin_data.phone,
        role="CLIENT_ADMIN",
        is_active=True
    )

    db.add(user)

    db.commit()

    db.refresh(user)

    return user





from app.utils.security import (
    verify_password
)

from app.utils.jwthandler import (
    create_token
)


def login_client_admin(
    db,
    email: str,
    password: str
):

    admin = (
        db.query(User)
        .filter(
            User.email == email,
            User.role == "CLIENT_ADMIN",
            User.is_active == True
        )
        .first()
    )

    if not admin:
        return None

    if not verify_password(
        password,
        admin.password_hash
    ):
        return None

    token = create_token(
        {
            "id": admin.id,
            "client_id": admin.client_id,
            "email": admin.email,
            "role": admin.role
        }
    )

    return token



from app.models.users import User


def get_client_admin_profile(
    db,
    user_id: str
):
    return (
        db.query(User)
        .filter(
            User.id == user_id,
            User.role == "CLIENT_ADMIN"
        )
        .first()
    )