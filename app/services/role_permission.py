import uuid

from fastapi import HTTPException

from app.models.roles import Role
from app.models.service_catalogue import ServiceCatalogue
from app.models.role_service_permissions import (
    RoleServicePermission
)

def assign_permissions_to_role(
    db,
    role_id: str,
    permission_data,
    current_user
):

    role = (
        db.query(Role)
        .filter(
            Role.id == role_id,
            Role.is_active == True
        )
        .first()
    )

    if not role:

        raise HTTPException(
            status_code=404,
            detail="Role not found"
        )

    if current_user["role"] != "ADMIN":

        if (
            role.client_id
            !=
            current_user["client_id"]
        ):

            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )

    created_permissions = []

    for permission in permission_data.permissions:

        service = (
            db.query(ServiceCatalogue)
            .filter(
                ServiceCatalogue.id
                ==
                permission.service_id,

                ServiceCatalogue.is_active
                ==
                True
            )
            .first()
        )

        if not service:

            raise HTTPException(
                status_code=404,
                detail=f"Service {permission.service_id} not found"
            )

        existing_permission = (
            db.query(
                RoleServicePermission
            )
            .filter(
                RoleServicePermission.role_id
                ==
                role_id,

                RoleServicePermission.service_id
                ==
                permission.service_id
            )
            .first()
        )

        if existing_permission:

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Permission already exists "
                    f"for service "
                    f"{permission.service_id}"
                )
            )

        role_permission = (
            RoleServicePermission(
                id=str(uuid.uuid4()),

                role_id=role_id,

                service_id=
                permission.service_id,

                can_create=
                permission.can_create,

                can_read=
                permission.can_read,

                can_update=
                permission.can_update,

                can_delete=
                permission.can_delete
            )
        )

        db.add(role_permission)

        created_permissions.append(
            role_permission
        )

    db.commit()

    for permission in created_permissions:

        db.refresh(permission)

    return created_permissions



    from fastapi import HTTPException

from app.models.roles import Role
from app.models.role_service_permissions import (
    RoleServicePermission
)

def get_role_permissions(
    db,
    role_id: str,
    current_user
):

    role = (
        db.query(Role)
        .filter(
            Role.id == role_id,
            Role.is_active == True
        )
        .first()
    )

    if not role:

        raise HTTPException(
            status_code=404,
            detail="Role not found"
        )

    if current_user["role"] != "ADMIN":

        if (
            role.client_id
            !=
            current_user["client_id"]
        ):

            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )

    permissions = (
        db.query(
            RoleServicePermission
        )
        .filter(
            RoleServicePermission.role_id
            ==
            role_id
        )
        .all()
    )

    return permissions



def update_role_permissions(
    db,
    role_id: str,
    permission_data,
    current_user
):

    role = (
        db.query(Role)
        .filter(
            Role.id == role_id,
            Role.is_active == True
        )
        .first()
    )

    if not role:

        raise HTTPException(
            status_code=404,
            detail="Role not found"
        )

    if current_user["role"] != "ADMIN":

        if (
            role.client_id
            !=
            current_user["client_id"]
        ):

            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )

    (
        db.query(
            RoleServicePermission
        )
        .filter(
            RoleServicePermission.role_id
            ==
            role_id
        )
        .delete()
    )

    created_permissions = []

    for permission in permission_data.permissions:

        service = (
            db.query(ServiceCatalogue)
            .filter(
                ServiceCatalogue.id
                ==
                permission.service_id,

                ServiceCatalogue.is_active
                ==
                True
            )
            .first()
        )

        if not service:

            raise HTTPException(
                status_code=404,
                detail=(
                    f"Service "
                    f"{permission.service_id}"
                    f" not found"
                )
            )

        role_permission = (
            RoleServicePermission(
                id=str(uuid.uuid4()),

                role_id=role_id,

                service_id=
                permission.service_id,

                can_create=
                permission.can_create,

                can_read=
                permission.can_read,

                can_update=
                permission.can_update,

                can_delete=
                permission.can_delete
            )
        )

        db.add(role_permission)

        created_permissions.append(
            role_permission
        )

    db.commit()

    for permission in created_permissions:

        db.refresh(permission)

    return created_permissions