import uuid

from fastapi import HTTPException

from app.models.asset_type import AssetType
from app.models.asset_categories import AssetCategory


def create_asset_type(
    db,
    type_data,
    current_user
):

    category = (
        db.query(AssetCategory)
        .filter(
            AssetCategory.id
            ==
            type_data.category_id,

            AssetCategory.client_id
            ==
            current_user["client_id"],

            AssetCategory.is_active
            ==
            True
        )
        .first()
    )

    if not category:

        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    existing_type = (
        db.query(AssetType)
        .filter(
            AssetType.client_id
            ==
            current_user["client_id"],

            AssetType.category_id
            ==
            type_data.category_id,

            AssetType.name
            ==
            type_data.name,

            AssetType.is_active
            ==
            True
        )
        .first()
    )

    if existing_type:

        raise HTTPException(
            status_code=400,
            detail="Type already exists"
        )

    asset_type = AssetType(

        id=str(uuid.uuid4()),

        client_id=current_user["client_id"],

        category_id=type_data.category_id,

        name=type_data.name,

        description=type_data.description,

        created_by=current_user["id"],

        is_active=True
    )

    db.add(asset_type)

    db.commit()

    db.refresh(asset_type)

    return asset_type



def get_asset_types(
    db,
    current_user
):

    return (
        db.query(AssetType)
        .filter(
            AssetType.client_id
            ==
            current_user["client_id"],

            AssetType.is_active
            ==
            True
        )
        .all()
    )



def get_asset_types_by_category(
    db,
    category_id: str,
    current_user
):

    return (
        db.query(AssetType)
        .filter(
            AssetType.client_id
            ==
            current_user["client_id"],

            AssetType.category_id
            ==
            category_id,

            AssetType.is_active
            ==
            True
        )
        .all()
    )


def get_asset_type_by_id(
    db,
    type_id: str,
    current_user
):

    asset_type = (
        db.query(AssetType)
        .filter(
            AssetType.id == type_id,
            AssetType.is_active == True
        )
        .first()
    )

    if not asset_type:
        raise HTTPException(
            status_code=404,
            detail="Asset type not found"
        )

    if (
        asset_type.client_id
        !=
        current_user["client_id"]
    ):
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    return asset_type



from fastapi import HTTPException

from app.models.asset_type import AssetType


def update_asset_type(
    db,
    type_id: str,
    type_data,
    current_user
):

    asset_type = (
        db.query(AssetType)
        .filter(
            AssetType.id == type_id,
            AssetType.is_active == True
        )
        .first()
    )

    if not asset_type:

        raise HTTPException(
            status_code=404,
            detail="Asset type not found"
        )

    if (
        asset_type.client_id
        !=
        current_user["client_id"]
    ):

        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    update_data = (
        type_data.model_dump(
            exclude_unset=True
        )
    )

    if "name" in update_data:

        existing_type = (
            db.query(AssetType)
            .filter(
                AssetType.client_id
                ==
                current_user["client_id"],

                AssetType.category_id
                ==
                asset_type.category_id,

                AssetType.name
                ==
                update_data["name"],

                AssetType.id
                !=
                type_id,

                AssetType.is_active
                ==
                True
            )
            .first()
        )

        if existing_type:

            raise HTTPException(
                status_code=400,
                detail="Asset type already exists"
            )

    for key, value in update_data.items():

        setattr(
            asset_type,
            key,
            value
        )

    db.commit()

    db.refresh(asset_type)

    return asset_type



from fastapi import HTTPException

from app.models.asset_type import AssetType


def deactivate_asset_type(
    db,
    type_id: str,
    current_user
):

    asset_type = (
        db.query(AssetType)
        .filter(
            AssetType.id == type_id,
            AssetType.is_active == True
        )
        .first()
    )

    if not asset_type:

        raise HTTPException(
            status_code=404,
            detail="Asset type not found"
        )

    if (
        asset_type.client_id
        !=
        current_user["client_id"]
    ):

        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    asset_type.is_active = False

    db.commit()

    db.refresh(asset_type)

    return asset_type