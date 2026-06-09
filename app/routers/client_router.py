from http.client import HTTPException

from fastapi import APIRouter
from sqlalchemy.orm import Session
from app.schemas.users import (
    ClientAdminLogin,
    TokenResponse
)
from app.services.user_service import (
    get_client_admin_profile
)

from app.schemas.users import (
    ClientAdminProfileResponse
)

from app.utils.auth import (
    client_admin_required
)


from app.services.departments import (
    get_departments_by_client
)

router = APIRouter(
    prefix="/client",
    tags=["Client"]
)

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.config.dependencies import get_db

from app.schemas.users import (
    ClientAdminCreate,
    UserResponse
)

from app.services.user_service import (
    create_client_admin
)

from app.utils.auth import (
    admin_required
)

router = APIRouter(
    prefix="/client",
    tags=["Client"]
)


@router.post(
    "/create-admin",
    response_model=UserResponse
)
def create_client_admin_route(
    admin_data: ClientAdminCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(admin_required)
):
    return create_client_admin(
        db,
        admin_data
    )




from app.services.user_service import (
    login_client_admin
)

router = APIRouter(
    prefix="/client-admin",
    tags=["Client Admin"]
)


@router.post(
    "/login",
    response_model=TokenResponse
)
def login(
    credentials: ClientAdminLogin,
    db: Session = Depends(get_db)
):

    token = login_client_admin(
        db,
        credentials.email,
        credentials.password
    )

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    return {
        "access_token": token,
        "token_type": "bearer"
    }

@router.get(
    "/me",
    response_model=ClientAdminProfileResponse
)
def get_profile(
    db: Session = Depends(get_db),
    current_user=Depends(
        client_admin_required
    )
):

    user = get_client_admin_profile(
        db,
        current_user["id"]
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Client Admin not found"
        )

    return user

