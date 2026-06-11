from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config.dependencies import get_db, get_current_user
from app.schemas.users import ManagerCreate, ManagerUpdate, UserCreate, UserResponse
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
    get_users,
    restore_manager,
    restore_user,
    update_manager,
)
from app.utils.auth import (
    admin_required,
    manager_create_required,
    manager_view_required,
)


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


# ── Managers ──────────────────────────────────────────────────────────────────

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

@router.post("", response_model=UserResponse)
def create_new_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user["role"] not in ["ADMIN", "CLIENT_ADMIN"]:
        raise HTTPException(status_code=403, detail="Access denied")

    return create_user(db, user_data, current_user)


@router.get("", response_model=list[UserResponse])
def fetch_users(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_users(db, current_user)


@router.get("/deactivated", response_model=list[UserResponse])
def fetch_deactivated_users(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_deactivated_users(db, current_user)


@router.get("/{user_id}", response_model=UserResponse)
def fetch_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_user_by_id(db, user_id, current_user)


@router.delete("/{user_id}", response_model=UserResponse)
def deactivate_existing_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return deactivate_user(db, user_id, current_user)


@router.patch("/{user_id}/restore", response_model=UserResponse)
def restore_existing_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return restore_user(db, user_id, current_user)