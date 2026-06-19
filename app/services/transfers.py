import uuid

from fastapi import HTTPException

from app.models.assets import Asset
from app.models.users import User
from app.models.transfers import Transfer
from app.models.departments import Department

def create_transfer(
    db,
    transfer_data,
    current_user
):

    asset = (
        db.query(Asset)
        .filter(
            Asset.id
            ==
            transfer_data.asset_id,
            Asset.is_active
            ==
            True
        )
        .first()
    )

    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Asset not found"
        )

    user = (
        db.query(User)
        .filter(
            User.id
            ==
            transfer_data.to_user_id,
            User.is_active
            ==
            True
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    if current_user["role"] == "MANAGER":

        department = (
            db.query(Department)
            .filter(
                Department.id
                ==
                asset.department_id,

                Department.manager_id
                ==
                current_user["id"],

                Department.is_active
                ==
                True
            )
            .first()
        )

        if not department:
            raise HTTPException(
                status_code=403,
                detail=(
                    "You can only transfer "
                    "assets of your department"
                )
            )

        if (
            user.department_id
            !=
            department.id
        ):
            raise HTTPException(
                status_code=403,
                detail=(
                    "Cannot transfer asset "
                    "outside your department"
                )
            )