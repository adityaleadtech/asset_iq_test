from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config.dependencies import get_db
from app.schemas.clients import ClientAdminUpdate
from app.schemas.users import (
    ClientAdminCreate,
    ClientAdminLogin,
    ClientAdminProfileResponse,
    TokenResponse,
    UserResponse,
    PasswordUpdateSchema,  # ← ADD THIS
)

from app.config.dependencies import (
    get_db,
    get_current_user
)
from app.services.client_services import (
    get_client_admin,
    get_client_admin_details,
    update_client_admin,
    update_admin_password,  # ← ADD THIS
    deactivate_admin,       # ← ADD THIS
    reactivate_admin,       # ← ADD THIS
    get_all_client_admins   # ← ADD THIS
)
from app.services.user_service import (
    create_client_admin,
    get_client_admin_profile,
    login_client_admin,
)
from app.utils.auth import admin_required, client_admin_required


router = APIRouter(
    prefix="/client",
    tags=["Client"],
)


@router.post("/create-admin", response_model=UserResponse)
def create_client_admin_route(
    admin_data: ClientAdminCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(admin_required),
):
    return create_client_admin(db, admin_data)

"""
@router.post("/login", response_model=TokenResponse)
def login(
    credentials: ClientAdminLogin,
    db: Session = Depends(get_db),
):
    token = login_client_admin(db, credentials.email, credentials.password)

    if not token:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"access_token": token, "token_type": "bearer"}

"""

@router.get("/me", response_model=ClientAdminProfileResponse)
def get_profile(
    db: Session = Depends(get_db),
    current_user=Depends(client_admin_required),
):
    user = get_client_admin_profile(db, current_user["id"])

    if not user:
        raise HTTPException(status_code=404, detail="Client Admin not found")

    return user


@router.get(
    "/{client_id}/admin",
    response_model=UserResponse
)
def fetch_client_admin(
    client_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
        get_current_user
    )
):

    return get_client_admin(
        db,
        client_id,
        current_user
    )


@router.patch(
    "/admin/{admin_id}",
    response_model=UserResponse
)
def update_client_admin_route(
    admin_id: str,
    admin_data: ClientAdminUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(
        admin_required
    )
):

    return update_client_admin(
        db,
        admin_id,
        admin_data
    )


# ============= NEW ENDPOINTS =============

@router.patch(
    "/admin/{admin_id}/password",
    response_model=UserResponse
)
def update_admin_password_route(
    admin_id: str,
    password_data: PasswordUpdateSchema,
    db: Session = Depends(get_db),
    current_admin=Depends(admin_required)
):
    """
    Change admin password
    
    Request body:
    {
        "password": "new_password"
    }
    """
    return update_admin_password(
        db,
        admin_id,
        password_data.password
    )


@router.patch(
    "/admin/{admin_id}/deactivate",
    response_model=UserResponse
)
def deactivate_admin_route(
    admin_id: str,
    db: Session = Depends(get_db),
    current_admin=Depends(admin_required)
):
    """
    Deactivate admin (soft delete)
    Sets is_active = False
    """
    return deactivate_admin(
        db,
        admin_id
    )


@router.patch(
    "/admin/{admin_id}/reactivate",
    response_model=UserResponse
)
def reactivate_admin_route(
    admin_id: str,
    db: Session = Depends(get_db),
    current_admin=Depends(admin_required)
):
    """
    Reactivate admin
    Sets is_active = True
    """
    return reactivate_admin(
        db,
        admin_id
    )


# ============= NEW ROUTE: Fetch All Admins =============

@router.get(
    "/{client_id}/admins/all",
    response_model=list[UserResponse]
)
def get_all_client_admins_route(
    client_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Get ALL admins for a client (including deactivated)
    Used to show reactivate button for inactive admins
    """
    return get_all_client_admins(db, client_id, current_user)