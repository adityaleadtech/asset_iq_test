from datetime import datetime
from enum import Enum
from pydantic import BaseModel


class LocationType(str, Enum):
    COUNTRY = "COUNTRY"
    STATE = "STATE"
    DISTRICT = "DISTRICT"
    CITY = "CITY"
    AREA = "AREA"
    BUILDING = "BUILDING"
    FLOOR = "FLOOR"
    OFFICE = "OFFICE"
    WAREHOUSE = "WAREHOUSE"
    ROOM = "ROOM"
    CABIN = "CABIN"
    OTHER = "OTHER"


class LocationNode(BaseModel):
    name: str
    location_type: LocationType


class LocationCreate(BaseModel):
    locations: list[LocationNode]

    code: str | None = None

    address_line_1: str | None = None
    address_line_2: str | None = None
    address_line_3: str | None = None

    postal_code: str | None = None

    latitude: float | None = None
    longitude: float | None = None

    radius_meters: int = 200

    description: str | None = None


class LocationResponse(BaseModel):
    id: str
    client_id: str
    parent_location_id: str | None = None

    name: str
    location_type: LocationType

    is_active: bool

    created_at: datetime
    updated_at: datetime | None = None

    model_config = {
        "from_attributes": True
    }


class LocationCreateResponse(BaseModel):
    message: str
    selected_location_id: str
    locations: list[LocationResponse]




class LocationDropdownResponse(BaseModel):
    id: str
    name: str
    location_type: LocationType

    model_config = {
        "from_attributes": True
    }


from pydantic import BaseModel


class LocationUpdate(BaseModel):
    name: str | None = None
    code: str | None = None

    address_line_1: str | None = None
    address_line_2: str | None = None
    address_line_3: str | None = None

    postal_code: str | None = None

    latitude: float | None = None
    longitude: float | None = None

    radius_meters: int | None = None

    description: str | None = None


class LocationResponse(BaseModel):
    id: str
    client_id: str
    parent_location_id: str | None = None

    name: str
    location_type: LocationType

    code: str | None = None

    address_line_1: str | None = None
    address_line_2: str | None = None
    address_line_3: str | None = None

    postal_code: str | None = None

    latitude: float | None = None
    longitude: float | None = None

    radius_meters: int | None = None

    description: str | None = None

    is_active: bool

    created_at: datetime
    updated_at: datetime | None = None

    model_config = {
        "from_attributes": True
    }


from pydantic import BaseModel
from app.enums.location_type import LocationType


class LocationUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    location_type: LocationType | None = None

    address_line_1: str | None = None
    address_line_2: str | None = None
    address_line_3: str | None = None

    postal_code: str | None = None

    latitude: float | None = None
    longitude: float | None = None
    radius_meters: int | None = None

    description: str | None = None


from pydantic import BaseModel
from typing import List
from app.enums.location_type import LocationType


class LocationPathNode(BaseModel):
    id: str
    name: str
    location_type: LocationType


class AssignableLocationResponse(BaseModel):
    id: str
    display_name: str
    path: List[LocationPathNode]