from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy.sql import func

from app.config.database import Base

from pydantic import BaseModel


class AssetCategoryCreate(
    BaseModel
):

    name: str

    description: str | None = None


class AssetCategoryUpdate(
    BaseModel
):

    name: str | None = None

    description: str | None = None


class AssetCategoryResponse(
    BaseModel
):

    id: str

    client_id: str

    name: str

    description: str | None

    is_active: bool

    created_by: str

    class Config:

        from_attributes = True


