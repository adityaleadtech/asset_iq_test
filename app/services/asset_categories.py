import uuid

from fastapi import HTTPException

from app.models.asset_categories import AssetCategory


def create_asset_category(
    db,
    category_data,
    current_user
):

    existing_category = (
        db.query(AssetCategory)
        .filter(
            AssetCategory.client_id
            ==
            current_user["client_id"],

            AssetCategory.name
            ==
            category_data.name,

            AssetCategory.is_active
            ==
            True
        )
        .first()
    )

    if existing_category:

        raise HTTPException(
            status_code=400,
            detail="Category already exists"
        )

    category = AssetCategory(

        id=str(uuid.uuid4()),

        client_id=current_user["client_id"],

        name=category_data.name,

        description=category_data.description,

        created_by=current_user["id"],

        is_active=True
    )

    db.add(category)

    db.commit()

    db.refresh(category)

    return category




def get_asset_categories(
    db,
    current_user
):

    return (
        db.query(AssetCategory)
        .filter(
            AssetCategory.client_id
            ==
            current_user["client_id"],

            AssetCategory.is_active
            ==
            True
        )
        .all()
    )



def get_asset_category_by_id(
    db,
    category_id: str,
    current_user
):

    category = (
        db.query(AssetCategory)
        .filter(
            AssetCategory.id
            ==
            category_id,

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

    if (
        category.client_id
        !=
        current_user["client_id"]
    ):

        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    return category




def update_asset_category(
    db,
    category_id: str,
    category_data,
    current_user
):

    category = get_asset_category_by_id(
        db,
        category_id,
        current_user
    )

    update_data = (
        category_data.model_dump(
            exclude_unset=True
        )
    )

    for key, value in update_data.items():

        setattr(
            category,
            key,
            value
        )

    db.commit()

    db.refresh(category)

    return category


def deactivate_asset_category(
    db,
    category_id: str,
    current_user
):

    category = get_asset_category_by_id(
        db,
        category_id,
        current_user
    )

    category.is_active = False

    db.commit()

    db.refresh(category)

    return category