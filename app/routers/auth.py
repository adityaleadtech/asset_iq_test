from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.config.dependencies import get_db

from app.schemas.auth import (
    ForgotPasswordRequest,
    ResetPasswordRequest
)

from app.services.auth import (
    forgot_password,
    reset_password
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/forgot-password")
def forgot_password_route(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    return forgot_password(
        db,
        request
    )

@router.post("/reset-password")
def reset_password_route(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    return reset_password(
        db,
        request
    )