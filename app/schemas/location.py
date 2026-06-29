from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.enums.location_type import (
    LocationType
)
from app.schemas.assets import LocationPathItem

class LocationCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description=(
            "Location name. "
            "Example: India, Pune, Office 12."
        ),
        examples=["India"]
    )

    location_type: LocationType = Field(
        ...,
        description=(
            "Location type. "
            "Available values: "
            "COUNTRY, STATE, DISTRICT, "
            "CITY, AREA, SITE, BUILDING, "
            "FLOOR, OFFICE, WAREHOUSE, OTHER."
        ),
        examples=["COUNTRY"]
    )

    parent_location_id: Optional[str] = Field(
        None,
        description=(
            "Parent location id. "
            "Keep null for root locations "
            "like COUNTRY."
        )
    )

    code: Optional[str] = Field(
        None,
        max_length=50,
        description=(
            "Optional location code."
        ),
        examples=["PUNE-HQ"]
    )

    postal_code: Optional[str] = Field(
        None,
        max_length=20,
        description=(
            "Postal or ZIP code."
        ),
        examples=["411057"]
    )

    latitude: Optional[float] = Field(
        None,
        description=(
            "Latitude of location."
        ),
        examples=[18.5912]
    )

    longitude: Optional[float] = Field(
        None,
        description=(
            "Longitude of location."
        ),
        examples=[73.7389]
    )

    radius_meters: int = Field(
        200,
        ge=1,
        description=(
            "Geofence radius in meters."
        ),
        examples=[200]
    )

    description: Optional[str] = Field(
        None,
        description=(
            "Optional description."
        ),
        examples=[
            "Main Office Building"
        ]
    )










class LocationUpdate(BaseModel):
    name: Optional[str] = None
    location_type: Optional[
        LocationType
    ] = None
    parent_location_id: Optional[
        str
    ] = None
    code: Optional[str] = None
    postal_code: Optional[
        str
    ] = None
    latitude: Optional[
        float
    ] = None
    longitude: Optional[
        float
    ] = None
    radius_meters: Optional[
        int
    ] = None
    description: Optional[
        str
    ] = None



class LocationDropdownResponse(
    BaseModel
):
        id: str
        name: str
        location_type: LocationType
        model_config = {
        "from_attributes": True
    }
        
class LocationResponse(
    BaseModel
):
    id: str
    client_id: str
    parent_location_id: Optional[
        str
    ]

    name: str
    normalized_name: str
    location_type: LocationType

    code: Optional[str]
    postal_code: Optional[str]

    latitude: Optional[
        float
    ]
    longitude: Optional[
        float
    ]

    radius_meters: int
    description: Optional[
        str
    ]

    is_active: bool

    created_at: datetime
    updated_at: Optional[
        datetime
    ]

    model_config = {
        "from_attributes": True
    }


class LocationPathNode(
    BaseModel
):
    id: str
    name: str
    location_type: LocationType


class LocationLeafPathResponse(
    BaseModel
):
    leaf_id: str
    leaf_name: str

    full_path: str

    path: list[
        LocationPathNode
    ]

class LocationListResponse(
    BaseModel
):
    items: list[
        LocationResponse
    ]

    page: int
    limit: int
    total: int
    total_pages: int


# app/schemas/location.py

class LocationPathNodeCreate(BaseModel):
    name: str
    location_type: LocationType


class LocationPathCreate(BaseModel):
    path: list[LocationPathNodeCreate]

class LocationPathNodeResponse(BaseModel):
    id: str
    name: str
    location_type: LocationType

    model_config = {
        "from_attributes": True
    }


class LocationPathResponse(BaseModel):
    leaf_id: str
    leaf_name: str
    full_path: str
    path: list[LocationPathNodeResponse]


# app/schemas/location.py

from pydantic import BaseModel
from app.enums.location_type import LocationType


class LocationDropdownResponse(BaseModel):
    id: str
    name: str
    location_type: LocationType
    parent_location_id: str | None = None

    model_config = {
        "from_attributes": True
    }


# schemas/location.py

class LocationMigrationRequest(BaseModel):
    source_location_id: str
    path: list[LocationPathItem]



class LocationPathNodeResponse(
    BaseModel
):
    id: str
    name: str
    location_type: LocationType

    model_config = {
        "from_attributes": True
    }


class LocationCardResponse(
    BaseModel
):
    id: str
    name: str
    location_type: LocationType

    full_path: str

    path: list[
        LocationPathNodeResponse
    ]

    model_config = {
        "from_attributes": True
    }