from enum import Enum


class LocationType(str, Enum):
    COUNTRY = "COUNTRY"
    STATE = "STATE"
    DISTRICT = "DISTRICT"
    CITY = "CITY"
    AREA = "AREA"
    SITE = "SITE"
    BUILDING = "BUILDING"
    FLOOR = "FLOOR"
    OFFICE = "OFFICE"
    WAREHOUSE = "WAREHOUSE"
    OTHER = "OTHER"