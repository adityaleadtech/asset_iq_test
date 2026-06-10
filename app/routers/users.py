from fastapi import APIRouter
from fastapi import Depends
from app.services.user_service import (
    create_manager,
    get_all_managers,
    get_managers_by_client_id,
    get_manager_by_id,
    update_manager,
    deactivate_manager
)


from app.services.user_service import (
    create_manager,
    get_all_managers,
    get_managers_by_client_id,
    get_manager_by_id,
    update_manager,
    deactivate_manager,
    get_deactivated_managers,
    restore_manager
)

from app.services.user_service import (
    create_manager,
    get_all_managers,
    get_managers_by_client_id,
    get_manager_by_id,
    update_manager,
    deactivate_manager,
    get_deactivated_managers
)

from sqlalchemy.orm import Session
from app.utils.auth import admin_required
from app.config.dependencies import get_db

from app.services.user_service import (
    create_manager,
    get_all_managers
)

from app.utils.auth import (
    manager_create_required,
    manager_view_required
)

from app.services.user_service import (
    create_manager,
    get_all_managers,
    get_managers_by_client_id
)


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

@router.post(
    "/managers",
    response_model=UserResponse
)
def create_new_manager(
    manager: ManagerCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        manager_create_required
    )
):

    return create_manager(
        db,
        manager,
        current_user
    )

from app.services.user_service import (
    create_manager,
    get_all_managers
)
from app.utils.auth import (
    manager_create_required,
    manager_view_required
)

@router.get(
    "/managers",
    response_model=list[UserResponse]
)
def fetch_managers(
    db: Session = Depends(get_db),
    current_user=Depends(
        manager_view_required
    )
):

    return get_all_managers(
        db,
        current_user
    )


@router.get(
    "/managers",
    response_model=list[UserResponse]
)
def fetch_managers(
    db: Session = Depends(get_db),
    current_user=Depends(
        manager_view_required
    )
):

    return get_all_managers(
        db,
        current_user
    )



@router.get(
    "/clients/{client_id}/managers",
    response_model=list[UserResponse]
)
def fetch_client_managers(
    client_id: str,
    db: Session = Depends(get_db),
    current_admin=Depends(
        admin_required
    )
):

    return get_managers_by_client_id(
        db,
        client_id
    )


from app.services.user_service import (
    create_manager,
    get_all_managers,
    get_managers_by_client_id,
    get_manager_by_id
)




@router.get(
    "/managers/deactivated",
    response_model=list[UserResponse]
)
def fetch_deactivated_managers(
    db: Session = Depends(get_db),
    current_user=Depends(
        manager_view_required
    )
):

    return get_deactivated_managers(
        db,
        current_user
    )
@router.get(
    "/managers/{manager_id}",
    response_model=UserResponse
)
def fetch_manager(
    manager_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
        manager_view_required
    )
):

    return get_manager_by_id(
        db,
        manager_id,
        current_user
    )


from app.services.user_service import (
    create_manager,
    get_all_managers,
    get_managers_by_client_id,
    get_manager_by_id,
    update_manager
)

from app.schemas.users import (
    ManagerCreate,
    ManagerUpdate,
    UserResponse
)


@router.patch(
    "/managers/{manager_id}",
    response_model=UserResponse
)
def update_existing_manager(
    manager_id: str,
    manager_data: ManagerUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        manager_view_required
    )
):

    return update_manager(
        db,
        manager_id,
        manager_data,
        current_user
    )


@router.delete(
    "/managers/{manager_id}"
)
def deactivate_existing_manager(
    manager_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
        manager_view_required
    )
):

    return deactivate_manager(
        db,
        manager_id,
        current_user
    )



@router.patch(
    "/managers/{manager_id}/restore",
    response_model=UserResponse
)
def restore_existing_manager(
    manager_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
        manager_view_required
    )
):

    return restore_manager(
        db,
        manager_id,
        current_user
    )