from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config.dependencies import get_db, get_current_user
from app.schemas.users import ManagerCreate, ManagerUpdate, UserCreate, UserResponse, UserUpdate
from app.services.user_service import (
    create_manager,
    create_user,
    deactivate_manager,
    deactivate_user,
    get_all_managers,
    get_deactivated_managers,
    get_deactivated_users,
    get_manager_by_id,
    get_managers_by_client_id,
    get_user_by_id,
    get_user_profile,
    get_users,
    restore_manager,
    restore_user,
    update_manager,
    update_user,
)
from app.utils.auth import (
    admin_required,
    manager_create_required,
    manager_view_required,
    service_permission_required,
)


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

@router.post(
    "",
    response_model=UserResponse
)
def create_new_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        service_permission_required(
            "USERS",
            "create"
        )
    )
):
   

    return create_user(db, user_data, current_user)


# ── Managers ──────────────────────────────────────────────────────────────────
@router.get(
    "/permission-test"
)


@router.get(
    "/me",
    response_model=UserResponse
)
def get_profile(

    db: Session = Depends(get_db),

    current_user=Depends(
        get_current_user
    )
):

    return get_user_profile(
        db,
        current_user["id"]
    )

@router.post("/managers", response_model=UserResponse)
def create_new_manager(
    manager: ManagerCreate,
    db: Session = Depends(get_db),
    current_user=Depends(manager_create_required),
):
    return create_manager(db, manager, current_user)


@router.get("/managers", response_model=list[UserResponse])
def fetch_managers(
    db: Session = Depends(get_db),
    current_user=Depends(manager_view_required),
):
    return get_all_managers(db, current_user)


@router.get("/managers/deactivated", response_model=list[UserResponse])
def fetch_deactivated_managers(
    db: Session = Depends(get_db),
    current_user=Depends(manager_view_required),
):
    return get_deactivated_managers(db, current_user)


@router.get("/managers/{manager_id}", response_model=UserResponse)
def fetch_manager(
    manager_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(manager_view_required),
):
    return get_manager_by_id(db, manager_id, current_user)


@router.patch("/managers/{manager_id}", response_model=UserResponse)
def update_existing_manager(
    manager_id: str,
    manager_data: ManagerUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(manager_view_required),
):
    return update_manager(db, manager_id, manager_data, current_user)


@router.delete("/managers/{manager_id}")
def deactivate_existing_manager(
    manager_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(manager_view_required),
):
    return deactivate_manager(db, manager_id, current_user)


@router.patch("/managers/{manager_id}/restore", response_model=UserResponse)
def restore_existing_manager(
    manager_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(manager_view_required),
):
    return restore_manager(db, manager_id, current_user)


@router.get("/clients/{client_id}/managers", response_model=list[UserResponse])
def fetch_client_managers(
    client_id: str,
    db: Session = Depends(get_db),
    current_admin=Depends(admin_required),
):
    return get_managers_by_client_id(db, client_id)


# ── Users ─────────────────────────────────────────────────────────────────────




@router.get(
    "",
    response_model=list[UserResponse]
)
def fetch_users(
    db: Session = Depends(get_db),
    current_user=Depends(
        service_permission_required(
            "USERS",
            "read"
        )
    )
):
    return get_users(
        db,
        current_user
    )


@router.get("/deactivated", response_model=list[UserResponse])
def fetch_deactivated_users(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_deactivated_users(db, current_user)


@router.get(
    "/{user_id}",
    response_model=UserResponse
)
def fetch_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
        service_permission_required(
            "USERS",
            "read"
        )
    )
):
    return get_user_by_id(
        db,
        user_id,
        current_user
    )
@router.delete(
    "/{user_id}",
    response_model=UserResponse
)
def deactivate_existing_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
        service_permission_required(
            "USERS",
            "delete"
        )
    )
):
    return deactivate_user(
        db,
        user_id,
        current_user
    )
@router.patch(
    "/{user_id}/restore",
    response_model=UserResponse
)
def restore_existing_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
        service_permission_required(
            "USERS",
            "update"
        )
    )
):
    return restore_user(
        db,
        user_id,
        current_user
    )


@router.patch(
    "/{user_id}",
    response_model=UserResponse
)
def update_existing_user(
    user_id: str,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        service_permission_required(
            "USERS",
            "update"
        )
    )
):
    return update_user(
        db,
        user_id,
        user_data,
        current_user
    )

from app.schemas.users import UserLogin
from app.services.user_service import (
    login_user
)
@router.post(
    "/login"
)
def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):

    token = login_user(
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




from app.schemas.users import (
    UserServiceResponse
)
from app.services.user_service import (
    get_user_services
)

@router.get(
    "/me/services",
    response_model=list[UserServiceResponse],
    summary="Fetch My Services",
    description="""
    Returns all services available to the currently logged-in user
    together with their CRUD permissions.

    Access:
    - USER
    - MANAGER
    - CLIENT_ADMIN

    Purpose:
    This endpoint should be called immediately after login.

    Frontend uses this API to:

    • Build sidebar menu
    • Show dashboard modules
    • Enable or disable buttons
    • Protect routes
    • Determine what actions the user can perform

    Example:

    User has access to:

    - User Management
    - Asset Management
    - Reports

    Then only those modules should be visible.

    Returned Permissions:

    can_create
    can_read
    can_update
    can_delete

    Example Use Case:

    USERS:
        can_create = true

    → User can create new users

    ASSET_MANAGEMENT:
        can_read = true

    → User can view assets

    REPORTS:
        can_read = false

    → Reports module should be hidden

    Recommended Frontend Flow:

    Login
        ↓
    GET /users/me
        ↓
    GET /users/me/services
        ↓
    Build dashboard dynamically
    """
)
def fetch_my_services(

    db: Session = Depends(get_db),

    current_user=Depends(
        get_current_user
    )
):

    return get_user_services(
        db,
        current_user
    )


