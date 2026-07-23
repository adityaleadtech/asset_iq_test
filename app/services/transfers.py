# app/services/transfers.py

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.transfers import Transfer
from app.models.location import Location
from app.models.departments import Department
from app.models.users import User
from app.models.asset import Asset
from app.schemas.transfers import AssetTransferRequest
from app.services.assets import get_asset_by_id


def transfer_asset(
    db: Session,
    asset_id: str,
    payload: AssetTransferRequest,
    current_user: dict
):
    """
    Transfer asset within the same client.

    Supports:
    - User -> User
    - Department -> Department
    - Location -> Location
    - Combination transfers
    """

    # Get asset as dictionary
    asset_dict = get_asset_by_id(
        db,
        asset_id,
        current_user
    )

    # Also get the ORM object for updating
    asset = (
        db.query(Asset)
        .filter(Asset.id == asset_id)
        .first()
    )

    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Asset not found"
        )

    #
    # Validate target location
    #
    location = None
    if payload.location_id:
        location = (
            db.query(Location)
            .filter(
                Location.id == payload.location_id,
                Location.is_active == True
            )
            .first()
        )

        if not location:
            raise HTTPException(
                status_code=404,
                detail="Location not found."
            )

        if location.client_id != asset.client_id:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Location must belong "
                    "to the same client."
                )
            )

    #
    # Validate target department
    #
    department = None
    if payload.department_id:
        department = (
            db.query(Department)
            .filter(
                Department.id
                == payload.department_id,
                Department.is_active == True
            )
            .first()
        )

        if not department:
            raise HTTPException(
                status_code=404,
                detail="Department not found."
            )

        if department.client_id != asset.client_id:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Department must belong "
                    "to the same client."
                )
            )

    #
    # Validate target user
    #
    user = None
    if payload.assigned_to_user_id:
        user = (
            db.query(User)
            .filter(
                User.id
                == payload.assigned_to_user_id,
                User.is_active == True
            )
            .first()
        )

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found."
            )

        if user.client_id != asset.client_id:
            raise HTTPException(
                status_code=400,
                detail=(
                    "User must belong "
                    "to the same client."
                )
            )

    #
    # Determine transfer type
    #
    changes = 0

    if payload.location_id:
        changes += 1

    if payload.department_id:
        changes += 1

    if payload.assigned_to_user_id:
        changes += 1

    if changes == 1:

        if payload.location_id:
            transfer_type = "LOCATION"

        elif payload.department_id:
            transfer_type = "DEPARTMENT"

        else:
            transfer_type = "USER"

    else:
        transfer_type = "MULTI"

    #
    # Create transfer record
    #
    transfer = Transfer(
        asset_id=asset.id,
        client_id=asset.client_id,
        
        from_location_id=asset.location_id,
        to_location_id=payload.location_id,
        
        from_department_id=asset.department_id,
        to_department_id=payload.department_id,
        
        from_user_id=asset.assigned_to_user_id,
        to_user_id=payload.assigned_to_user_id,
        
        transfer_type=transfer_type,
        transfer_reason=payload.transfer_reason,
        notes=payload.notes,
        
        transferred_by=current_user["id"],
        status="COMPLETED"
    )

    db.add(transfer)

    #
    # Update asset
    #
    if payload.location_id:
        asset.location_id = payload.location_id

    if payload.department_id:
        asset.department_id = payload.department_id

    if payload.assigned_to_user_id:
        asset.assigned_to_user_id = payload.assigned_to_user_id

    db.commit()
    db.refresh(asset)

    # Return the updated asset dict
    return get_asset_by_id(db, asset_id, current_user)