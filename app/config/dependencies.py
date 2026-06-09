from app.config.database import SessionLocal
from fastapi import Depends
from fastapi import Depends
from fastapi import HTTPException
from fastapi.security import HTTPBearer
from fastapi.security import HTTPAuthorizationCredentials

from app.utils.jwthandler import verify_token


oauth2_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        oauth2_scheme
    )
):

    token = credentials.credentials

    payload = verify_token(token)

    if payload is None:

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    return payload

def get_db():
    db= SessionLocal()
    try:
        yield db
    finally:
        db.close()

