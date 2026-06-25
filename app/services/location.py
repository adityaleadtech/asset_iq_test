from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.enums.location_type import LocationType
from app.models.location import Location
from app.schemas.location import LocationCreate


# ============================================
# CREATE LOCATION - EXPORTED FUNCTION
# ============================================
def create_location(
    db: Session,
    payload: LocationCreate,
    client_id: str
):
    """
    Creates a location hierarchy.
    Existing nodes are reused instead of duplicated.
    """

    if not payload.locations:
        raise HTTPException(
            status_code=400,
            detail="At least one location is required."
        )

    parent_id = None
    selected_locations = []

    try:
        for node in payload.locations:

            name = node.name.strip()

            # Check if location already exists
            existing = (
                db.query(Location)
                .filter(
                    Location.client_id == client_id,
                    Location.parent_location_id == parent_id,
                    Location.name == name,
                    Location.location_type == node.location_type,
                    Location.is_active == True
                )
                .first()
            )

            # Reuse existing location
            if existing:
                selected_locations.append(existing)
                parent_id = existing.id
                continue

            # Create new location
            location = Location(
                client_id=client_id,
                parent_location_id=parent_id,
                name=name,
                location_type=node.location_type,
                code=payload.code
            )

            db.add(location)
            db.flush()

            selected_locations.append(location)
            parent_id = location.id

        db.commit()

        for location in selected_locations:
            db.refresh(location)

        return {
            "message": "Location hierarchy ready.",
            "selected_location_id": selected_locations[-1].id,
            "locations": selected_locations
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create locations: {str(e)}"
        )

# ============================================
# GET LOCATIONS DROPDOWN - EXPORTED FUNCTION
# ============================================
def get_locations_dropdown(
    db: Session,
    client_id: str,
    location_type: LocationType,
    parent_location_id: str | None
):
    query = db.query(Location).filter(
        Location.client_id == client_id,
        Location.location_type == location_type,
        Location.is_active == True
    )

    if parent_location_id:
        query = query.filter(
            Location.parent_location_id == parent_location_id
        )
    else:
        query = query.filter(
            Location.parent_location_id.is_(None)
        )

    return query.order_by(Location.name).all()


# ============================================
# GET LOCATION BY ID
# ============================================
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


# ============================================
# UPDATE LOCATION
# ============================================
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

    updates = payload.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(location, field, value)

    db.commit()
    db.refresh(location)

    return location


# ============================================
# DELETE LOCATION
# ============================================
def delete_location(
    db: Session,
    location_id: str,
    client_id: str
):
    from app.models.asset import Asset
    from app.models.departments import Department
    
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

    # Check for active child locations
    child_count = (
        db.query(Location)
        .filter(
            Location.parent_location_id == location_id,
            Location.is_active == True
        )
        .count()
    )

    if child_count > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete location because child locations exist."
        )

    # Check assets
    asset_count = (
        db.query(Asset)
        .filter(Asset.location_id == location_id)
        .count()
    )

    if asset_count > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete location because assets are assigned to it."
        )

    # Check departments
    department_count = (
        db.query(Department)
        .filter(Department.location_id == location_id)
        .count()
    )

    if department_count > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete location because departments are assigned to it."
        )

    # Soft delete
    location.is_active = False
    db.commit()

    return {
        "message": "Location deleted successfully."
    }


def get_all_locations(
    db: Session,
    client_id: str
):
    locations = (
        db.query(Location)
        .filter(
            Location.client_id == client_id,
            Location.is_active == True
        )
        .order_by(
            Location.created_at.asc()
        )
        .all()
    )

    return locations



def update_location(
    db: Session,
    location_id: str,
    payload: LocationUpdate,
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


def update_location(
    db: Session,
    location_id: str,
    payload: LocationUpdate,
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

def get_client_locations(
    db: Session,
    client_id: str
):
    locations = (
        db.query(Location)
        .filter(
            Location.client_id == client_id,
            Location.is_active == True
        )
        .all()
    )

    location_map = {
        location.id: location
        for location in locations
    }

    # All locations that have a parent
    parent_ids = {
        location.parent_location_id
        for location in locations
        if location.parent_location_id
    }

    results = []

    for location in locations:

        # Skip non-leaf nodes
        if location.id in parent_ids:
            continue

        path = []
        current = location

        while current:
            path.append({
                "id": current.id,
                "name": current.name,
                "location_type": current.location_type
            })

            current = location_map.get(
                current.parent_location_id
            )

        path.reverse()

        results.append({
            "id": location.id,
            "display_name": " > ".join(
                node["name"]
                for node in path
            ),
            "path": path
        })

    return results