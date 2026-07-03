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
    response_model=RoleResponse,
    summary="Create a new role, accessible to client admins",
    description="This endpoint allows client admins to create a new role within the system. The role will be associated with the client of the current user. A Role is a custom name for the services that will be associated with them"
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
    response_model=list[RoleResponse],
    summary="Fetch all roles, accessible to client admins",
    description="This endpoint allows client admins to fetch all roles associated with their client. The roles will be filtered based on the client of the current user."
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
    ,summary="fetch custom role by id, accessible to client admins",
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