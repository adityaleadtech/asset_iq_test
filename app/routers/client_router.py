from fastapi import APIRouter
from sqlalchemy.orm import Session

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