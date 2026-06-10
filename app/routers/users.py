from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.config.dependencies import get_db

from app.schemas.users import (
    ManagerCreate,
    UserResponse
)

from app.services.user_service import (
    create_manager
)

from app.utils.auth import (
    manager_create_required
)

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)