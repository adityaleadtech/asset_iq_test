from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator
import re


# ============================================================
# Request Schemas
# ============================================================

class AttendanceCheckIn(BaseModel):
    """Request body for employee check-in."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

    @field_validator('latitude')
    def validate_latitude(cls, v):
        if v < -90 or v > 90:
            raise ValueError('Latitude must be between -90 and 90')
        return v

    @field_validator('longitude')
    def validate_longitude(cls, v):
        if v < -180 or v > 180:
            raise ValueError('Longitude must be between -180 and 180')
        return v


class AttendanceCheckOut(BaseModel):
    """Request body for employee check-out."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

    @field_validator('latitude')
    def validate_latitude(cls, v):
        if v < -90 or v > 90:
            raise ValueError('Latitude must be between -90 and 90')
        return v

    @field_validator('longitude')
    def validate_longitude(cls, v):
        if v < -180 or v > 180:
            raise ValueError('Longitude must be between -180 and 180')
        return v


# ============================================================
# Response Schemas
# ============================================================

class AttendanceResponse(BaseModel):
    """Response schema for attendance records."""
    id: str
    
    attendance_date: date
    
    user_id: str
    user_name: str
    
    office_timing_id: str
    office_timing_name: str
    
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    
    check_in_latitude: Optional[float] = None
    check_in_longitude: Optional[float] = None
    
    # ✅ NEW - GPS accuracy fields
    check_in_accuracy: Optional[float] = None
    
    check_out_latitude: Optional[float] = None
    check_out_longitude: Optional[float] = None
    
    # ✅ NEW - GPS accuracy fields
    check_out_accuracy: Optional[float] = None
    
    working_minutes: int
    
    status: str  # PRESENT, LATE, HALF_DAY, ABSENT
    
    # ✅ NEW - boolean flags
    is_late: bool = False
    is_half_day: bool = False
    
    remarks: Optional[str] = None
    
    # ✅ NEW - checkout notes
    check_out_notes: Optional[str] = None
    
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class AttendanceHistoryResponse(BaseModel):
    """Paginated response for attendance history."""
    items: List[AttendanceResponse]
    total: int
    page: int
    size: int


class AttendanceSummaryResponse(BaseModel):
    """Summary statistics for attendance."""
    total_employees: int
    present_today: int
    late_today: int
    absent_today: int
    half_day_today: int  # ✅ Changed from on_leave_today
    overall_attendance_percentage: float


class AttendanceDashboardResponse(BaseModel):
    """Dashboard response for attendance."""
    today_summary: AttendanceSummaryResponse
    weekly_attendance: List[dict]  # List of {date: str, present: int, absent: int, late: int, half_day: int}
    monthly_attendance: List[dict]  # List of {week: str, present: int, absent: int, late: int, half_day: int}


# ============================================================
# Filter and Admin Schemas
# ============================================================

class AttendanceFilterParams(BaseModel):
    """Filter parameters for admin attendance listing."""
    user_id: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None  # PRESENT, LATE, HALF_DAY, ABSENT
    department_id: Optional[str] = None
    office_timing_id: Optional[str] = None  # ✅ CHANGED: location_id -> office_timing_id
    
    @field_validator('office_timing_id')
    def validate_office_timing_id(cls, v):
        if v is not None and not re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', v, re.I):
            raise ValueError('Invalid office timing ID format')
        return v


# ============================================================
# Admin Request Schemas
# ============================================================

class AdminAttendanceCreate(BaseModel):
    """Admin creating attendance record for a user."""
    user_id: str
    office_timing_id: str
    attendance_date: date
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    check_in_latitude: Optional[float] = None
    check_in_longitude: Optional[float] = None
    check_out_latitude: Optional[float] = None
    check_out_longitude: Optional[float] = None
    status: str = "PRESENT"
    remarks: Optional[str] = None
    
    @field_validator('user_id')
    def validate_user_id(cls, v):
        if not re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', v, re.I):
            raise ValueError('Invalid user ID format')
        return v

    @field_validator('office_timing_id')
    def validate_office_timing_id(cls, v):
        if not re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', v, re.I):
            raise ValueError('Invalid office timing ID format')
        return v

    @field_validator('attendance_date')
    def validate_attendance_date(cls, v):
        if v > date.today():
            raise ValueError('Attendance date cannot be in the future')
        return v


class AdminAttendanceUpdate(BaseModel):
    """Admin updating attendance record."""
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    check_in_latitude: Optional[float] = None
    check_in_longitude: Optional[float] = None
    check_out_latitude: Optional[float] = None
    check_out_longitude: Optional[float] = None
    status: Optional[str] = None
    remarks: Optional[str] = None
    working_minutes: Optional[int] = Field(None, ge=0)


# ============================================================
# Statistics Schemas
# ============================================================

class UserAttendanceStats(BaseModel):
    """Attendance statistics for a single user."""
    user_id: str
    user_name: str
    total_days: int
    present_days: int
    late_days: int
    half_days: int
    absent_days: int
    attendance_percentage: float
    total_working_minutes: int
    average_working_minutes: float


class MonthlyAttendanceStats(BaseModel):
    """Monthly attendance statistics."""
    month: int
    year: int
    total_employees: int
    total_working_days: int
    total_present: int
    total_late: int
    total_half_day: int
    total_absent: int
    overall_attendance_percentage: float


class EmployeeAttendanceReport(BaseModel):
    """Detailed attendance report for an employee."""
    user_id: str
    user_name: str
    email: str
    department_name: Optional[str] = None
    office_timing_name: Optional[str] = None
    period_start: date
    period_end: date
    summary: UserAttendanceStats
    daily_records: List[AttendanceResponse]


# ============================================================
# Geofencing Schemas
# ============================================================

class GeofenceValidationRequest(BaseModel):
    """Request to validate if a location is within office geofence."""
    user_id: str
    latitude: float
    longitude: float


class GeofenceValidationResponse(BaseModel):
    """Response for geofence validation."""
    is_within_radius: bool
    distance_from_office: float  # in meters
    office_timing_id: str
    office_timing_name: str
    office_latitude: float
    office_longitude: float
    allowed_radius: int
    message: str