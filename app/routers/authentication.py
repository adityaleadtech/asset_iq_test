from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.config.dependencies import get_db

from app.schemas.login import (
    LoginRequest,
    LoginResponse
)

from app.services.login import login


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Common Login",
    description="""
Authenticate any user in the system.

### Login Flow

1. Checks Platform Admin table
2. If not found, checks Users table
3. Verifies password
4. Generates JWT
5. Returns authenticated user details

### Supported Roles

- Platform Admin
- Client Admin
- Manager
- User

The frontend does not need to know which table the account belongs to.
""",
    responses={
        200: {
            "description": "Login Successful"
        },
        401: {
            "description": "Invalid Email or Password"
        }
    }
)
def login_user(
    payload: LoginRequest,
    db: Session = Depends(get_db)
):

    return login(
        db=db,
        payload=payload
    )