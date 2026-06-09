from fastapi import Depends
from fastapi import HTTPException
from fastapi.security import HTTPBearer

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