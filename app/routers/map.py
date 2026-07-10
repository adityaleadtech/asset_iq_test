from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.dependencies import get_db
from app.models.asset import Asset
from app.models.departments import Department
from app.schemas.map import (
    AssetMapItem,
    AssetMapResponse
)
from app.utils.auth import (
    service_permission_required
)


router = APIRouter(
    prefix="/map",
    tags=["Map"]
)


@router.get(
    "/asset",
    summary="Get Assets for Map"
)
def asset_map(
    db: Session = Depends(get_db),
    current_user=Depends(
        service_permission_required(
            "ASSET_MANAGEMENT",
            "read"
        )
    ),
    client_id: str | None = None
):
    assets = get_locations(
        db,
        current_user,
        client_id
    )

    response = [
        asset
        for asset in assets
    ]

    return response


def get_locations(
    db: Session,
    current_user: dict,
    client_id: str | None = None
):
    """
    Get assets with location data.

    ADMIN:
    - Gets assets for selected client.

    CLIENT_ADMIN:
    - Gets all assets of their client.

    MANAGER:
    - Gets assets of their department.

    USER:
    - Gets assets assigned to them.
    """

    role = current_user.get("role")

    user_client_id = current_user.get(
        "client_id"
    )

    user_id = current_user.get("id")

    #
    # ADMIN
    #
    if role == "ADMIN":
        print("++++++++++++++++++++++++++HIT++++++++++++++++++++++++++++++++++++++++++++++++++++")
        if client_id:
            return db.query(Asset).filter(
                client_id==Asset.client_id,
                Asset.current_longitude.isnot(
                    None
                ),
                Asset.current_latitude.isnot(
                    None
                ),
                Asset.current_longitude != 0,
                Asset.current_latitude != 0,
               
                Asset.is_active.is_(True)
            )
        return (
            db.query(Asset)
            .filter(
                Asset.current_longitude.isnot(
                    None
                ),
                Asset.current_latitude.isnot(
                    None
                ),
                Asset.current_longitude != 0,
                Asset.current_latitude != 0,
               
                Asset.is_active.is_(True)
            )
            .all()
        )

    #
    # CLIENT ADMIN
    #
    if role == "CLIENT_ADMIN":
        return (
            db.query(Asset)
            .filter(
                Asset.current_longitude.isnot(
                    None
                ),
                Asset.current_latitude.isnot(
                    None
                ),
                Asset.current_longitude != 0,
                Asset.current_latitude != 0,
                Asset.client_id
                == user_client_id,
                Asset.is_active.is_(True)
            )
            .all()
        )

    #
    # MANAGER
    #
    if role == "MANAGER":
        department = (
            db.query(Department)
            .filter(
                Department.client_id
                == user_client_id,
                Department.manager_id
                == user_id
            )
            .first()
        )

        if not department:
            return []

        return (
            db.query(Asset)
            .filter(
                Asset.current_longitude.isnot(
                    None
                ),
                Asset.current_latitude.isnot(
                    None
                ),
                Asset.current_longitude != 0,
                Asset.current_latitude != 0,
                Asset.department_id
                == department.id,
                Asset.client_id
                == user_client_id,
                Asset.is_active.is_(True)
            )
            .all()
        )

    #
    # USER
    #
    return (
        db.query(Asset)
        .filter(
            Asset.current_longitude.isnot(
                None
            ),
            Asset.current_latitude.isnot(
                None
            ),
            Asset.current_longitude != 0,
            Asset.current_latitude != 0,
            Asset.client_id
            == user_client_id,
            Asset.assigned_to_user_id
            == user_id,
            Asset.is_active.is_(True)
        )
        .all()
    )