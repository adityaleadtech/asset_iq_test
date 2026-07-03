from pydantic import BaseModel
from typing import List, Optional

class AssetMap(BaseModel):
    asset_id: str
    current_latitude: float  # ✅ Changed to float
    current_longitude: float  # ✅ Changed to float
    name: Optional[str] = None
    location_id: Optional[str] = None

class AssetMapResponse(BaseModel):
    assets: List[AssetMap]