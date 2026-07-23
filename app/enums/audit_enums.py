from enum import Enum


# ==========================================================
# Audit Plan Frequency
# ==========================================================

class AuditFrequencyUnit(str, Enum):
    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"


# ==========================================================
# Audit Location Status
# ==========================================================

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
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"


# ==========================================================
# Audit Target Types
# ==========================================================

class AuditTargetType(str, Enum):
    LOCATION = "LOCATION"
    DEPARTMENT = "DEPARTMENT"
    CATEGORY = "CATEGORY"
    ASSET = "ASSET"


# ==========================================================
# Audit Result Status
# ==========================================================

class AuditResultStatus(str, Enum):
    PENDING = "PENDING"
    IN_PLACE = "IN_PLACE"
    DISLOCATED = "DISLOCATED"
    LOST = "LOST"
    NOT_FOUND = "NOT_FOUND"
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
    PENDING = "PENDING"
    IN_PLACE = "IN_PLACE"
    DISLOCATED = "DISLOCATED"
    LOST = "LOST"
    NOT_FOUND = "NOT_FOUND"


# ==========================================================
# Asset Condition Status
# ==========================================================

class AuditConditionStatus(str, Enum):
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    FAIR = "FAIR"
    DAMAGED = "DAMAGED"
    BROKEN = "BROKEN"


# ==========================================================
# Asset Condition Status (for mobile app - more detailed)
# ==========================================================

class AssetConditionStatus(str, Enum):
    """Physical condition of the asset - used by mobile app"""
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    FAIR = "FAIR"
    POOR = "POOR"
    DAMAGED = "DAMAGED"
    VERY_POOR = "VERY_POOR"


# ==========================================================
# Location Status (for mobile app)
# ==========================================================

class LocationStatus(str, Enum):
    """GPS location verification status - used by mobile app"""
    VERIFIED = "VERIFIED"
    NEARBY = "NEARBY"
    OUTSIDE_GEOFENCE = "OUTSIDE_GEOFENCE"
    LOCATION_UNKNOWN = "LOCATION_UNKNOWN"