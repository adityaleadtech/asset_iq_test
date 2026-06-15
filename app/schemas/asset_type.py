from pydantic import BaseModel


class AssetTypeCreate(
    BaseModel
):

    category_id: str

    name: str

    description: str | None = None


class AssetTypeUpdate(
    BaseModel
):

    name: str | None = None

    description: str | None = None


class AssetTypeResponse(
    BaseModel
):

    id: str

    client_id: str

    category_id: str

    name: str

    description: str | None

    is_active: bool

    created_by: str

    class Config:

        from_attributes = True