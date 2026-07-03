from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session
from fastapi import HTTPException


from app.schemas.platform_admin import PlatformAdminLogin
from app.schemas.platform_admin import TokenResponse
from app.services.platform_admin_service import (
    login_platform_admin
)
from app.config.dependencies import get_db
from app.services.platform_admin_service import get_all_platform_admins
from app.schemas.platform_admin import PlatformAdminResponse
from app.schemas.platform_admin import PlatformAdminCreation
from app.services.platform_admin_service import create_platform_admin

router= APIRouter(
    prefix="/platform-admins",
    tags=["Platform Admins"]
)

@router.get("/",
            response_model=list[PlatformAdminResponse])
def fetch_all_PlatformAdmins(db:Session=Depends(get_db)):
    return get_all_platform_admins(db)


@router.post("/create",response_model=PlatformAdminResponse)
def createAdmin(admin:PlatformAdminCreation,db:Session=Depends(get_db)):
    return create_platform_admin(db,admin)




"""
@router.post(
    "/login",
    response_model=TokenResponse
)
def login(
    credentials: PlatformAdminLogin,
    db: Session = Depends(get_db)
):
    token = login_platform_admin(
        db,
        credentials.email,
        credentials.password
    )

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    return {
        "access_token": token,
        "token_type": "bearer"
    }


"""