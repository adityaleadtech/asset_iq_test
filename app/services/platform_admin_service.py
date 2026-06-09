import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.platform_admin import PlatformAdmin
from app.utils.security import hash_password
from app.utils.security import verify_password
from app.utils.jwthandler import create_token

def get_all_platform_admins(db:Session):
    return db.query(PlatformAdmin).all()


def create_platform_admin(db,platform_admin_data):
    admin= PlatformAdmin(
        id=str(uuid.uuid4()),
        email=platform_admin_data.email,
        password_hash=hash_password(platform_admin_data.password_hash),
        full_name=platform_admin_data.full_name,
        is_active=True,
        role=platform_admin_data.role,
        

    )
    db.add(admin)
    db.commit()
    db.refresh(admin)

    return admin

def login_platform_admin(
    db,
    email: str,
    password: str
):
    admin = (
        db.query(PlatformAdmin)
        .filter(
            PlatformAdmin.email == email
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
    if admin.role != "ADMIN":
        return None

    token = create_token(
        {
            "id": admin.id,
            "email": admin.email,
            "role":admin.role
        }
    )

    return token

