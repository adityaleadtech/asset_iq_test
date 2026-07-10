from decimal import Decimal

from pydantic import BaseModel, Field


class AssetMapItem(BaseModel):
    asset_id: str

    current_latitude: Decimal
    current_longitude: Decimal

    model_config = {
        "from_attributes": True
    }


class AssetMapResponse(BaseModel):
    assets: list[AssetMapItem] = Field(
        default_factory=list
    )