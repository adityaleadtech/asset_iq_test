from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.config.dependencies import (
    get_current_user,
    get_db
)


from app.schemas.roles import (
    RoleCreate,
    RoleResponse,
    RoleUpdate
)

from app.services.roles import (
    create_role,
    deactivate_role,
    get_deactivated_roles,
    get_roles,
    get_role_by_id,
    restore_role
)


from app.utils.auth import (
    
    client_admin_required)


router = APIRouter(
    prefix="/roles",
    tags=["Roles"]
)

@router.post(
    "",
    response_model=RoleResponse
)
def create_new_role(
    role: RoleCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        client_admin_required
    )
):

    return create_role(
        db,
        role,
        current_user
    )



from app.services.roles import (
    create_role,
    get_roles
)

@router.get(
    "",
    response_model=list[RoleResponse]
)
def fetch_roles(
    db: Session = Depends(get_db),
    current_user=Depends(
        get_current_user
    )
):

    return get_roles(
        db,
        current_user
    )


@router.get(
    "/{role_id}",
    response_model=RoleResponse
)
def fetch_role(
    role_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
        get_current_user
    )
):

    return get_role_by_id(
        db,
        role_id,
        current_user
    )



from app.services.roles import (
    create_role,
    get_roles,
    get_role_by_id,
    update_role
)

@router.patch(
    "/{role_id}",
    response_model=RoleResponse
)
def update_existing_role(
    role_id: str,
    role_data: RoleUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        get_current_user
    )
):

    return update_role(
        db,
        role_id,
        role_data,
        current_user
    )


@router.delete(
    "/{role_id}",
    response_model=RoleResponse
)
def delete_role(
    role_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
        get_current_user
    )
):

    return deactivate_role(
        db,
        role_id,
        current_user
    )


@router.patch(
    "/{role_id}/restore",
    response_model=RoleResponse
)
def restore_existing_role(
    role_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
        get_current_user
    )
):

    return restore_role(
        db,
        role_id,
        current_user
    )


@router.get(
    "/deactivated",
    response_model=list[RoleResponse]
)
def fetch_deactivated_roles(
    db: Session = Depends(get_db),
    current_user=Depends(
        get_current_user
    )
):

    return get_deactivated_roles(
        db,
        current_user
    )