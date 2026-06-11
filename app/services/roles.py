import uuid

from fastapi import HTTPException

from app.models.roles import Role


def create_role(
    db,
    role_data,
    current_user
):

    role = Role(
        id=str(uuid.uuid4()),
        client_id=current_user["client_id"],
        name=role_data.name,
        description=role_data.description,
        is_active=True
    )

    db.add(role)

    db.commit()

    db.refresh(role)

    return role



def get_roles(
    db,
    current_user
):

    if current_user["role"] == "ADMIN":

        return (
            db.query(Role)
            .filter(
                Role.is_active == True
            )
            .all()
        )

    return (
        db.query(Role)
        .filter(
            Role.client_id ==
            current_user["client_id"],

            Role.is_active == True
        )
        .all()
    )


from fastapi import HTTPException

def get_role_by_id(
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

    return role


def update_role(
    db,
    role_id: str,
    role_data,
    current_user
):

    role = (
        db.query(Role)
        .filter(
            Role.id == role_id
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

    update_data = role_data.model_dump(
        exclude_unset=True
    )

    for key, value in update_data.items():

        setattr(
            role,
            key,
            value
        )

    db.commit()

    db.refresh(role)

    return role


from app.services.roles import (
    create_role,
    get_roles,
    get_role_by_id,
    update_role
)

def update_role(
    db,
    role_id: str,
    role_data,
    current_user
):

    role = (
        db.query(Role)
        .filter(
            Role.id == role_id
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

    update_data = role_data.model_dump(
        exclude_unset=True
    )

    for key, value in update_data.items():

        setattr(
            role,
            key,
            value
        )

    db.commit()

    db.refresh(role)

    return role

def deactivate_role(
    db,
    role_id: str,
    current_user
):

    role = (
        db.query(Role)
        .filter(
            Role.id == role_id
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

    role.is_active = False

    db.commit()

    db.refresh(role)

    return role



def restore_role(
    db,
    role_id: str,
    current_user
):

    role = (
        db.query(Role)
        .filter(
            Role.id == role_id
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

    role.is_active = True

    db.commit()

    db.refresh(role)

    return role

def get_deactivated_roles(
    db,
    current_user
):

    if current_user["role"] == "ADMIN":

        return (
            db.query(Role)
            .filter(
                Role.is_active == False
            )
            .all()
        )

    return (
        db.query(Role)
        .filter(
            Role.client_id ==
            current_user["client_id"],

            Role.is_active == False
        )
        .all()
    )