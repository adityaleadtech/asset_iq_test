import uuid

from fastapi import HTTPException

from app.models.service_catalogue import (
    ServiceCatalogue
)
from app.services.assets import get_asset_by_id


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


from sqlalchemy.orm import Session
from app.models.asset import AssetScanLog
from app.services.assets import get_asset_by_id


def get_asset_audits(
    db: Session,
    asset_id: str,
    current_user: dict
):
    """
    Fetch complete scan history of an asset.
    """

    asset = get_asset_by_id(
        db,
        asset_id,
        current_user
    )

    audits = (
        db.query(AssetScanLog)
        .filter(
            AssetScanLog.asset_id == asset.id
        )
        .order_by(
            AssetScanLog.scanned_at.desc()
        )
        .all()
    )

    return audits


from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.location import Location


def get_location_by_id(
    db: Session,
    location_id: str,
    client_id: str
):
    location = (
        db.query(Location)
        .filter(
            Location.id == location_id,
            Location.client_id == client_id,
            Location.is_active == True
        )
        .first()
    )

    if not location:
        raise HTTPException(
            status_code=404,
            detail="Location not found."
        )

    return location

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.location import Location

def update_location(
    db: Session,
    location_id: str,
    payload,
    client_id: str
):
    location = (
        db.query(Location)
        .filter(
            Location.id == location_id,
            Location.client_id == client_id,
            Location.is_active == True
        )
        .first()
    )

    if not location:
        raise HTTPException(
            status_code=404,
            detail="Location not found."
        )

    updates = payload.model_dump(
        exclude_unset=True
    )

    for field, value in updates.items():
        setattr(location, field, value)

    db.commit()
    db.refresh(location)

    return location

def delete_location(
    db: Session,
    location_id: str,
    client_id: str
):
    location = (
        db.query(Location)
        .filter(
            Location.id == location_id,
            Location.client_id == client_id,
            Location.is_active == True
        )
        .first()
    )

    if not location:
        raise HTTPException(
            status_code=404,
            detail="Location not found."
        )

    active_children = (
        db.query(Location)
        .filter(
            Location.parent_location_id == location_id,
            Location.is_active == True
        )
        .count()
    )

    if active_children:
        raise HTTPException(
            status_code=400,
            detail=(
                "Cannot delete location because "
                "child locations exist."
            )
        )

    if location.assets:
        raise HTTPException(
            status_code=400,
            detail=(
                "Cannot delete location because "
                "assets are assigned."
            )
        )

    if location.departments:
        raise HTTPException(
            status_code=400,
            detail=(
                "Cannot delete location because "
                "departments are assigned."
            )
        )

    location.is_active = False

    db.commit()

    return {
        "message": "Location deleted successfully."
    }