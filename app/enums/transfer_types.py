from enum import Enum

class TransferType(str, Enum):
    DEPARTMENT = "DEPARTMENT"
    LOCATION = "LOCATION"
    USER = "USER"