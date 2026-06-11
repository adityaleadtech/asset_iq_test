from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.config.dependencies import (
    get_db,
    get_current_user
)

from app.schemas.role_permissions import (
    RolePermissionCreate,
    RoleServicePermissionResponse
)

from app.services.role_permission import (
    assign_permissions_to_role
)


router = APIRouter(
    prefix="/roles",
    tags=["Role Permissions"]
)

@router.post(
    "/{role_id}/permissions",
    response_model=list[
        RoleServicePermissionResponse
    ]
)
def assign_role_permissions(
    role_id: str,
    permission_data: RolePermissionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        get_current_user
    )
):

    return assign_permissions_to_role(
        db,
        role_id,
        permission_data,
        current_user
    )


from app.services.role_permission import (
    assign_permissions_to_role,
    get_role_permissions
)


@router.get(
    "/{role_id}/permissions",
    response_model=list[
        RoleServicePermissionResponse
    ]
)
def fetch_role_permissions(
    role_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
        get_current_user
    )
):

    return get_role_permissions(
        db,
        role_id,
        current_user
    )


from app.services.role_permission import (
    assign_permissions_to_role,
    get_role_permissions,
    update_role_permissions
)

@router.patch(
    "/{role_id}/permissions",
    response_model=list[
        RoleServicePermissionResponse
    ]
)
def update_permissions(
    role_id: str,
    permission_data: RolePermissionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        get_current_user
    )
):

    return update_role_permissions(
        db,
        role_id,
        permission_data,
        current_user
    )