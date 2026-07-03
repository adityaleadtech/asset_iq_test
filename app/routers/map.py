from app.models.asset import Asset
from app.models.departments import Department
from app.models.users import User
from app.schemas.map import AssetMap, AssetMapResponse
from app.utils.auth import service_permission_required
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config.dependencies import (
    get_db,
    get_current_user
)

router = APIRouter(
    prefix="/map",
    tags=["Map"]
)

@router.get("/asset", response_model=AssetMapResponse)  # ✅ Changed from response_class to response_model
def asset_map(
    db: Session = Depends(get_db),
    current_user = Depends(
        service_permission_required(
            "ASSET_MANAGEMENT",
            "read"
        )
    ),
    client_id: str | None = None
):
    assets = get_locations(db, current_user, client_id)

    response = [
        AssetMap(
            asset_id=asset.id,
            current_latitude=asset.current_latitude,
            current_longitude=asset.current_longitude,
        )
        for asset in assets
    ]
    return AssetMapResponse(assets=response)


def get_locations(db: Session, current_user: dict, client_id: str | None = None):
    """
    Get assets with location data based on user role:
    - ADMIN: All assets of the client
    - CLIENT_ADMIN: All assets of the client
    - MANAGER: All assets of their department
    - USER: All assets assigned to them
    """
    
    # ADMIN with specific client_id
    if current_user.get("role") == "ADMIN" and client_id is not None:
        assets = db.query(Asset).filter(
            Asset.current_longitude != 0,
            Asset.current_latitude != 0,
            Asset.client_id == client_id
        ).all()
        return assets
    
    # CLIENT_ADMIN - gets all assets of their client
    if current_user.get("role") == "CLIENT_ADMIN":
        client_id = current_user.get("client_id")
        assets = db.query(Asset).filter(
            Asset.current_longitude != 0,
            Asset.current_latitude != 0,
            Asset.client_id == client_id
        ).all()
        return assets
    
    # MANAGER - gets assets of their department
    if current_user.get("role") == "MANAGER":
        department = db.query(Department).filter(
            Department.client_id == current_user.get("client_id"),
            Department.manager_id == current_user.get("id")
        ).first()
        
        if not department:
            return []  # Return empty list if no department found
        
        assets = db.query(Asset).filter(
            Asset.current_longitude != 0,
            Asset.current_latitude != 0,
            Asset.department_id == department.id
        ).all()
        return assets
    
    # Regular USER - gets assets assigned to them
    assets = db.query(Asset).filter(
        Asset.current_longitude != 0,
        Asset.current_latitude != 0,
        Asset.client_id == current_user.get("client_id"),
        Asset.assigned_to_user_id == current_user.get("id")
    ).all()
    return assets