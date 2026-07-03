from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.departments import Department
from app.models.location import Location
from app.schemas.location import LocationCreate, LocationMigrationRequest, LocationPathCreate
from app.enums.location_type import (
    LocationType
)


def create_location(
    db: Session,
    payload: LocationCreate,
    current_user: dict
):
    """
    Create a location.

    Rules:
    - Names are automatically converted to UPPERCASE.
    - Duplicate locations are not created.
    - COUNTRY and OTHER can be root locations.
    - All other location types require a parent.
    - Parent location must belong to the same client.
    """

    # --------------------------------
    # Resolve Client
    # --------------------------------
    client_id = current_user.get(
        "client_id"
    )

    if not client_id:
        raise HTTPException(
            status_code=400,
            detail=(
                "Client context is required."
            )
        )

    # --------------------------------
    # Normalize Name
    # --------------------------------
    normalized_name = (
        payload.name
        .strip()
        .upper()
    )

    if not normalized_name:
        raise HTTPException(
            status_code=400,
            detail=(
                "Location name cannot "
                "be empty."
            )
        )

    # --------------------------------
    # Root Validation
    # --------------------------------
    root_types = {
        LocationType.COUNTRY,
        LocationType.OTHER
    }

    if (
        not payload.parent_location_id
        and payload.location_type
        not in root_types
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                f"{payload.location_type.value} "
                "must have a parent location."
            )
        )

    # --------------------------------
    # Parent Validation
    # --------------------------------
    parent = None

    if payload.parent_location_id:

        parent = (
            db.query(Location)
            .filter(
                Location.id
                ==
                payload.parent_location_id,
                Location.is_active
                ==
                True
            )
            .first()
        )

        if not parent:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Parent location "
                    "not found."
                )
            )

        if (
            parent.client_id
            != client_id
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Parent location "
                    "belongs to another "
                    "client."
                )
            )

    # --------------------------------
    # Duplicate Check
    # --------------------------------
    existing = (
        db.query(Location)
        .filter(
            Location.client_id
            ==
            client_id,

            Location.parent_location_id
            ==
            payload.parent_location_id,

            Location.location_type
            ==
            payload.location_type,

            Location.normalized_name
            ==
            normalized_name,

            Location.is_active
            ==
            True
        )
        .first()
    )

    # Already exists
    if existing:
        return existing

    # --------------------------------
    # Create Location
    # --------------------------------
    location = Location(
        client_id=client_id,
        parent_location_id=
        payload.parent_location_id,

        name=normalized_name,
        normalized_name=
        normalized_name,

        location_type=
        payload.location_type,

        code=payload.code,
        postal_code=
        payload.postal_code,

        latitude=
        payload.latitude,

        longitude=
        payload.longitude,

        radius_meters=
        payload.radius_meters,

        description=
        payload.description
    )

    # --------------------------------
    # Save
    # --------------------------------
    try:
        db.add(location)
        db.commit()
        db.refresh(location)

    except Exception:
        db.rollback()
        raise

    return location



def create_location_path(
    db: Session,
    payload: LocationPathCreate,
    current_user: dict,
    c_id: str | None = None
):
    client_id = current_user.get("client_id")   
    if current_user.get("role") == "ADMIN" and c_id:
        client_id = c_id

    if not payload.path:
        raise HTTPException(
            status_code=400,
            detail="Path cannot be empty."
        )

    parent_id = None
    created_path = []

    try:
        for node in payload.path:

            normalized_name = (
                node.name
                .strip()
                .upper()
            )

            if not normalized_name:
                raise HTTPException(
                    status_code=400,
                    detail="Location name cannot be empty."
                )

            location = (
                db.query(Location)
                .filter(
                    Location.client_id
                    == client_id,
                    Location.parent_location_id
                    == parent_id,
                    Location.location_type
                    == node.location_type,
                    Location.normalized_name
                    == normalized_name,
                    Location.is_active
                    == True
                )
                .first()
            )

            #
            # Create if missing
            #
            if not location:
                location = Location(
                    client_id=client_id,
                    parent_location_id=parent_id,
                    name=normalized_name,
                    normalized_name=normalized_name,
                    location_type=node.location_type
                )

                db.add(location)
                db.flush()

            created_path.append({
                "id": location.id,
                "name": location.name,
                "location_type":
                    location.location_type
            })

            parent_id = location.id

        db.commit()

        leaf = created_path[-1]

        return {
            "leaf_id": leaf["id"],
            "leaf_name": leaf["name"],
            "full_path": " > ".join(
                node["name"]
                for node in created_path
            ),
            "path": created_path
        }

    except Exception:
        db.rollback()
        raise



def get_location_dropdown(
    db: Session,
    current_user: dict,
    parent_location_id: str | None,
    location_type: LocationType | None,
    search: str | None,
    client_id: str | None = None
):
    # Determine the client ID to use
    if client_id:
        used_client_id = client_id
    else:
        used_client_id = current_user.get("client_id")

    query = (
        db.query(Location)
        .filter(
            Location.client_id
            ==
            used_client_id,
            Location.is_active
            ==
            True
        )
    )

    #
    # Parent Filter
    #
    if parent_location_id:
        query = query.filter(
            Location.parent_location_id
            ==
            parent_location_id
        )
    else:
        query = query.filter(
            Location.parent_location_id
            .is_(None)
        )

    #
    # Type Filter
    #
    if location_type:
        query = query.filter(
            Location.location_type
            ==
            location_type
        )

    #
    # Search
    #
    if search:
        query = query.filter(
            Location.normalized_name.ilike(
                f"%{search.strip().upper()}%"
            )
        )

    return (
        query
        .order_by(Location.name)
        .all()
    )



def get_location_leaf_path(
    db: Session,
    location_id: str,
    current_user: dict,
    client_id: str | None = None
):
    
    if current_user["role"] !="ADMIN":
        print("CALEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEED")
        client_id = client_id or current_user.get("client_id")
        location = (
        db.query(Location)
        .filter(
            Location.id == location_id,
            Location.client_id== client_id,
            Location.is_active == True
        )
        .first()
    )
        if not location:
            raise HTTPException(
            status_code=404,
            detail="Location not found."
        )

        path = []

        current = location

        while current is not None:
            path.insert(0, {
            "id": current.id,
            "name": current.name,
            "location_type":
                current.location_type
        })

            current = current.parent

        return {
        "leaf_id": location.id,
        "leaf_name": location.name,
        "full_path": " > ".join(
            item["name"]
            for item in path
            ),
        "path": path
        }
    if current_user["role"] =="ADMIN":

        location = (
        db.query(Location)  
        .filter(
            Location.id == location_id,
            Location.is_active == True
        )
        .first()
    )
        if not location:
            raise HTTPException(
            status_code=404,
            detail="Location not found."
        )

        path = []

        current = location

        while current is not None:
            path.insert(0, {
            "id": current.id,
            "name": current.name,
            "location_type":
                current.location_type
        })

            current = current.parent

        return {
        "leaf_id": location.id,
        "leaf_name": location.name,
        "full_path": " > ".join(
            item["name"]
            for item in path
            ),
        "path": path
        }




def migrate_location(
    db: Session,
    location_id: str,
    payload: LocationPathCreate,
    current_user: dict
):
    source = (
        db.query(Location)
        .filter(
            Location.id == location_id,
            Location.client_id
            == current_user["client_id"],
            Location.is_active == True
        )
        .first()
    )

    if not source:
        raise HTTPException(
            status_code=404,
            detail="Location not found."
        )

    #
    # Create/find hierarchy
    #
    destination = create_location_path(
        db,
        payload,
        current_user
    )

    destination_id = (
        destination["leaf_id"]
    )

    #
    # Same location
    #
    if destination_id == source.id:
        raise HTTPException(
            status_code=400,
            detail=(
                "Destination location "
                "cannot be same as "
                "source location."
            )
        )

    #
    # Move assets
    #
    assets_migrated = (
        db.query(Asset)
        .filter(
            Asset.location_id
            == source.id,
            Asset.is_active == True
        )
        .update(
            {
                Asset.location_id:
                destination_id
            },
            synchronize_session=False
        )
    )

    #
    # Move departments
    #
    departments_migrated = (
        db.query(Department)
        .filter(
            Department.location_id
            == source.id,
            Department.is_active == True
        )
        .update(
            {
                Department.location_id:
                destination_id
            },
            synchronize_session=False
        )
    )

    #
    # Close old location
    #
    source.is_active = False

    db.commit()

    return {
        "message":
        "Location migrated successfully.",
        "old_location_id":
        source.id,
        "new_location_id":
        destination_id,
        "assets_migrated":
        assets_migrated,
        "departments_migrated":
        departments_migrated
    }



# services/location_service.py

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.location import Location
from app.models.asset import Asset


def migrate_location(
    db: Session,
    payload: LocationMigrationRequest,
    current_user: dict,
):
    # ----------------------------------
    # Validate source location
    # ----------------------------------
    source_location = (
        db.query(Location)
        .filter(
            Location.id
            == payload.source_location_id
        )
        .first()
    )

    if not source_location:
        raise HTTPException(
            status_code=404,
            detail="Source location not found."
        )

    if (
        current_user["role"] != "ADMIN"
        and source_location.client_id
        != current_user["client_id"]
    ):
        raise HTTPException(
            status_code=403,
            detail="Access denied."
        )

    # ----------------------------------
    # Create new hierarchy
    # ----------------------------------
    parent_id = None
    created_locations = []

    for item in payload.path:
        existing = (
            db.query(Location)
            .filter(
                Location.client_id
                == source_location.client_id,
                Location.parent_id
                == parent_id,
                Location.name
                == item.name,
                Location.location_type
                == item.location_type,
                Location.is_active
                == True
            )
            .first()
        )

        if existing:
            location = existing
        else:
            location = Location(
                name=item.name,
                location_type=item.location_type,
                client_id=source_location.client_id,
                parent_id=parent_id,
                is_active=True,
            )

            db.add(location)
            db.flush()

        created_locations.append(location)
        parent_id = location.id

    destination_location = created_locations[-1]

    # ----------------------------------
    # Move assets
    # ----------------------------------
    (
        db.query(Asset)
        .filter(
            Asset.location_id
            == source_location.id
        )
        .update(
            {
                Asset.location_id:
                destination_location.id
            },
            synchronize_session=False
        )
    )

    # ----------------------------------
    # Deactivate old location
    # ----------------------------------
    source_location.is_active = False

    db.commit()

    db.refresh(destination_location)

    return {
        "message":
            "Location migrated successfully.",
        "source_location_id":
            source_location.id,
        "destination_location_id":
            destination_location.id,
    }



def deactivate_location_tree(
    db: Session,
    location: Location
):
    #
    # Assets
    #
    db.query(Asset).filter(
        Asset.location_id == location.id,
        Asset.is_active == True
    ).update(
        {
            Asset.is_active: False
        },
        synchronize_session=False
    )

    #
    # Departments
    #
    db.query(Department).filter(
        Department.location_id == location.id,
        Department.is_active == True
    ).update(
        {
            Department.is_active: False
        },
        synchronize_session=False
    )

    #
    # Children
    #
    children = (
        db.query(Location)
        .filter(
            Location.parent_location_id
            == location.id,
            Location.is_active == True
        )
        .all()
    )

    for child in children:
        deactivate_location_tree(
            db,
            child
        )

    #
    # Location
    #
    location.is_active = False



def close_location(
    db: Session,
    location_id: str,
    current_user: dict
):
    location = (
        db.query(Location)
        .filter(
            Location.id == location_id,
            Location.client_id
            == current_user["client_id"],
            Location.is_active == True
        )
        .first()
    )

    if not location:
        raise HTTPException(
            status_code=404,
            detail="Location not found."
        )

    deactivate_location_tree(
        db,
        location
    )

    db.commit()

    return {
        "message":
        "Location closed successfully."
    }




def get_location_cards(
    db: Session,
    current_user: dict,
    client_id: str | None = None
):
    #
    # Get only leaf locations
    #
    client_id = client_id or current_user.get("client_id")
    leaf_locations = (
        db.query(Location)
        .filter(
            Location.client_id
            ==
            client_id,
            Location.is_active
            ==
            True,
            ~Location.children.any(
                Location.is_active
                ==
                True
            )
        )
        .order_by(
            Location.name
        )
        .all()
    )

    response = []

    for location in leaf_locations:

        path = []

        current = location

        while current:

            path.insert(
                0,
                {
                    "id":
                    current.id,
                    "name":
                    current.name,
                    "location_type":
                    current.location_type
                }
            )

            current = current.parent

        response.append(
            {
                "id":
                location.id,
                "name":
                location.name,
                "location_type":
                location.location_type,
                "full_path":
                " > ".join(
                    item["name"]
                    for item in path
                ),
                "path":
                path
            }
        )

    return response