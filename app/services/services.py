import uuid

from fastapi import HTTPException

from app.models.service_catalogue import (
    ServiceCatalogue
)


def create_service(
    db,
    service_data
):

    existing_service = (
        db.query(ServiceCatalogue)
        .filter(
            ServiceCatalogue.code ==
            service_data.code
        )
        .first()
    )

    if existing_service:

        raise HTTPException(
            status_code=400,
            detail="Service already exists"
        )

    service = ServiceCatalogue(
        id=str(uuid.uuid4()),
        code=service_data.code,
        name=service_data.name,
        description=service_data.description,
        is_active=True
    )

    db.add(service)

    db.commit()

    db.refresh(service)

    return service




def get_all_services(db):

    return (
        db.query(ServiceCatalogue)
        .filter(
            ServiceCatalogue.is_active == True
        )
        .all()
    )


def get_service_by_id(
    db,
    service_id: str
):

    service = (
        db.query(ServiceCatalogue)
        .filter(
            ServiceCatalogue.id == service_id,
            ServiceCatalogue.is_active == True
        )
        .first()
    )

    if not service:

        raise HTTPException(
            status_code=404,
            detail="Service not found"
        )

    return service



def update_service(
    db,
    service_id: str,
    service_data
):

    service = (
        db.query(ServiceCatalogue)
        .filter(
            ServiceCatalogue.id == service_id
        )
        .first()
    )

    if not service:

        raise HTTPException(
            status_code=404,
            detail="Service not found"
        )

    update_data = service_data.model_dump(
        exclude_unset=True
    )

    if "code" in update_data:

        existing_service = (
            db.query(ServiceCatalogue)
            .filter(
                ServiceCatalogue.code ==
                update_data["code"],
                ServiceCatalogue.id != service_id
            )
            .first()
        )

        if existing_service:

            raise HTTPException(
                status_code=400,
                detail="Service code already exists"
            )

    for key, value in update_data.items():

        setattr(
            service,
            key,
            value
        )

    db.commit()

    db.refresh(service)

    return service



def deactivate_service(
    db,
    service_id: str
):

    service = (
        db.query(ServiceCatalogue)
        .filter(
            ServiceCatalogue.id == service_id,
            ServiceCatalogue.is_active == True
        )
        .first()
    )

    if not service:

        raise HTTPException(
            status_code=404,
            detail="Service not found"
        )

    service.is_active = False

    db.commit()

    db.refresh(service)

    return service



def restore_service(
    db,
    service_id: str
):

    service = (
        db.query(ServiceCatalogue)
        .filter(
            ServiceCatalogue.id == service_id,
            ServiceCatalogue.is_active == False
        )
        .first()
    )

    if not service:

        raise HTTPException(
            status_code=404,
            detail="Service not found"
        )

    service.is_active = True

    db.commit()

    db.refresh(service)

    return service


def get_deactivated_services(db):

    return (
        db.query(ServiceCatalogue)
        .filter(
            ServiceCatalogue.is_active == False
        )
        .all()
    )

import uuid

from fastapi import HTTPException

from app.models.users import User
from app.models.roles import Role
from app.models.service_catalogue import ServiceCatalogue
from app.models.role_service_permissions import (
    RoleServicePermission
)

from app.utils.security import (
    hash_password
)

