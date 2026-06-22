import secrets

from datetime import datetime
from datetime import timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.users import User
from app.schemas.auth import ForgotPasswordRequest
from app.utils.emails import send_reset_email
from app.config.settings import settings



def forgot_password(
    db: Session,
    request: ForgotPasswordRequest
):
    user = (
        db.query(User)
        .filter(
            User.email == request.email,
            User.is_active == True
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    token = secrets.token_urlsafe(32)

    user.password_reset_token = token
    user.password_reset_expires_at = (
        datetime.utcnow()
        + timedelta(minutes=15)
    )

    db.commit()

    reset_link = (
        f"{settings.FRONTEND_URL}"
        f"/reset-password"
        f"?token={token}"
    )

    send_reset_email(
        user.email,
        reset_link
    )

    return {
        "message":
        "Password reset link sent successfully."
    }


from app.schemas.auth import ResetPasswordRequest
from app.utils.security import hash_password


def reset_password(
    db: Session,
    request: ResetPasswordRequest
):
    user = (
        db.query(User)
        .filter(
            User.password_reset_token
            == request.token
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid token"
        )

    if (
        user.password_reset_expires_at
        < datetime.utcnow()
    ):
        raise HTTPException(
            status_code=400,
            detail="Token expired"
        )

    user.password_hash = hash_password(
        request.new_password
    )

    user.password_reset_token = None
    user.password_reset_expires_at = None

    db.commit()

    return {
        "message":
        "Password reset successful."
    }