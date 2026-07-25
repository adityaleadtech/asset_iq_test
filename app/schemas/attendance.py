from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


# ============================================================
# Request Schemas
# ============================================================

class AttendanceCheckIn(BaseModel):
    """Request body for employee check-in."""
    latitude: float
    longitude: float


class AttendanceCheckOut(BaseModel):
    """Request body for employee check-out."""
    latitude: float
    longitude: float


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
    
    check_out_latitude: Optional[float] = None
    check_out_longitude: Optional[float] = None
    
    working_minutes: int
    
    status: str  # PRESENT, LATE, HALF_DAY, ABSENT, ON_LEAVE
    
    remarks: Optional[str] = None
    
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
    on_leave_today: int
    half_day_today: int
    overall_attendance_percentage: float


class AttendanceDashboardResponse(BaseModel):
    """Dashboard response for attendance."""
    today_summary: AttendanceSummaryResponse
    weekly_attendance: List[dict]  # List of {date: str, present: int, absent: int}
    monthly_attendance: List[dict]  # List of {week: str, present: int, absent: int}


class AttendanceFilterParams(BaseModel):
    """Filter parameters for admin attendance listing."""
    user_id: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None  # PRESENT, LATE, HALF_DAY, ABSENT, ON_LEAVE
    department_id: Optional[str] = None
    location_id: Optional[str] = None