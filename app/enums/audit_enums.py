from enum import Enum


# ==========================================================
# Audit Plan Frequency
# ==========================================================

class AuditFrequencyUnit(str, Enum):
    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"

class AuditLocationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    NEARBY = "NEARBY"
    OUTSIDE_GEOFENCE = "OUTSIDE_GEOFENCE"
    LOCATION_UNKNOWN = "LOCATION_UNKNOWN"
# ==========================================================
# Audit Plan Status
# ==========================================================

class AuditPlanStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


# ==========================================================
# Audit Target Types
# ==========================================================

class AuditTargetType(str, Enum):
    LOCATION = "LOCATION"
    DEPARTMENT = "DEPARTMENT"
    CATEGORY = "CATEGORY"
    ASSET = "ASSET"


from enum import Enum

class AuditResultStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
# ==========================================================
# Audit Session Status
# ==========================================================

class AuditSessionStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"


# ==========================================================
# Asset Audit Status
# ==========================================================

class AuditAssetStatus(str, Enum):
    IN_PLACE = "IN_PLACE"
    DISLOCATED = "DISLOCATED"
    LOST = "LOST"
    NOT_FOUND = "NOT_FOUND"


# ==========================================================
# Asset Condition
# ==========================================================

class AuditConditionStatus(str, Enum):
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    FAIR = "FAIR"
    DAMAGED = "DAMAGED"
    BROKEN = "BROKEN"