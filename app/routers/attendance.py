# app/routers/attendance.py

from datetime import date
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    Query,
    status,
)

from sqlalchemy.orm import Session

from app.config.dependencies import get_db
from app.config.dependencies import get_current_user

from app.schemas.attendance import (
    AttendanceCheckIn,
    AttendanceCheckOut,
    AttendanceResponse,
    AttendanceHistoryResponse,
    AttendanceDashboardResponse,
    AttendanceFilterParams,
    AttendanceSummaryResponse,
)

from app.services.attendance import AttendanceService


# ============================================================
# Router
# ============================================================

router = APIRouter(
    prefix="/attendance",
    tags=["Attendance"],
)


# ============================================================
# Employee APIs (For All Users)
# ============================================================

@router.post(
    "/check-in",
    response_model=AttendanceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Employee check-in",
    description="Record employee check-in with location coordinates.",
)
def check_in(
    payload: AttendanceCheckIn,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Check in for the day.
    
    **Allowed Roles:** USER, MANAGER, CLIENT_ADMIN
    
    - **USER**: Regular employee
    - **MANAGER**: Can check in
    - **CLIENT_ADMIN**: Can check in (for testing/demo purposes)
    
    Validates user role, prevents duplicate check-in, determines attendance status,
    and records check-in location.
    """
    return AttendanceService.check_in(
        payload=payload,
        db=db,
        current_user=current_user,
    )


@router.post(
    "/check-out",
    response_model=AttendanceResponse,
    summary="Employee check-out",
    description="Record employee check-out with location coordinates.",
)
def check_out(
    payload: AttendanceCheckOut,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Check out for the day.
    
    **Allowed Roles:** USER, MANAGER, CLIENT_ADMIN
    
    - **USER**: Regular employee
    - **MANAGER**: Can check out
    - **CLIENT_ADMIN**: Can check out (for testing/demo purposes)
    
    Requires existing check-in, calculates working minutes,
    and records check-out location.
    """
    return AttendanceService.check_out(
        payload=payload,
        db=db,
        current_user=current_user,
    )


@router.get(
    "/me",
    response_model=AttendanceResponse,
    summary="Get today's attendance",
    description="Get current user's attendance record for today.",
)
def get_my_attendance(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Get today's attendance record for the authenticated user.
    
    **Allowed Roles:** USER, MANAGER, CLIENT_ADMIN
    
    Returns the complete attendance record including check-in/out times,
    status, location data, and working minutes.
    """
    return AttendanceService.get_my_attendance(
        db=db,
        current_user=current_user,
    )


@router.get(
    "/history",
    response_model=AttendanceHistoryResponse,
    summary="Get attendance history",
    description="Get paginated attendance history for the current user.",
)
def get_my_attendance_history(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Get attendance history with pagination.
    
    **Allowed Roles:** USER, MANAGER, CLIENT_ADMIN
    
    Returns all attendance records for the current user with date range filtering.
    """
    return AttendanceService.get_my_attendance_history(
        db=db,
        current_user=current_user,
        page=page,
        size=size,
        start_date=start_date,
        end_date=end_date,
    )


# ============================================================
# Admin APIs (Admin Only)
# ============================================================

@router.get(
    "",
    response_model=AttendanceHistoryResponse,
    summary="Get all attendance records",
    description="Get all attendance records with filtering (Admin only).",
)
def get_all_attendance(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    
    # Filters
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    department_id: Optional[str] = Query(None, description="Filter by department ID"),
    location_id: Optional[str] = Query(None, description="Filter by location ID"),
    status: Optional[str] = Query(None, description="Filter by status (PRESENT, LATE, HALF_DAY, ABSENT)"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Get all attendance records with comprehensive filtering.
    
    **Admin Only** - Requires PLATFORM_ADMIN or CLIENT_ADMIN role.
    
    - **Platform Admin**: Can view all attendance records across all clients
    - **Client Admin**: Can view only their client's attendance records
    
    Available filters: user_id, department_id, location_id, status, start_date, end_date
    """
    # Check admin permissions
    if current_user.get("role") not in ["PLATFORM_ADMIN", "CLIENT_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required to view all attendance records."
        )
    
    filters = AttendanceFilterParams(
        user_id=user_id,
        department_id=department_id,
        location_id=location_id,
        status=status,
        start_date=start_date,
        end_date=end_date,
    )

    return AttendanceService.get_all_attendance(
        db=db,
        current_user=current_user,
        page=page,
        size=size,
        filters=filters,
    )


@router.get(
    "/dashboard",
    response_model=AttendanceDashboardResponse,
    summary="Get attendance dashboard",
    description="Get attendance statistics and analytics (Admin only).",
)
def get_attendance_dashboard(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Get comprehensive attendance dashboard statistics.
    
    **Admin Only** - Requires PLATFORM_ADMIN or CLIENT_ADMIN role.
    
    - **Platform Admin**: Sees data for all clients
    - **Client Admin**: Sees data for their client only
    
    Returns today's summary, weekly trend, monthly trend, and attendance percentage.
    """
    # Check admin permissions
    if current_user.get("role") not in ["PLATFORM_ADMIN", "CLIENT_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required to view dashboard."
        )
    
    return AttendanceService.get_attendance_dashboard(
        db=db,
        current_user=current_user,
    )


@router.get(
    "/user/{user_id}",
    response_model=AttendanceHistoryResponse,
    summary="Get user attendance",
    description="Get attendance history for a specific user (Admin only).",
)
def get_user_attendance(
    user_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Get attendance history for a specific user.
    
    **Admin Only** - Requires PLATFORM_ADMIN or CLIENT_ADMIN role.
    
    - **Platform Admin**: Can view any user's attendance
    - **Client Admin**: Can view only users in their client
    
    Useful for managers to review employee attendance.
    """
    # Check admin permissions
    if current_user.get("role") not in ["PLATFORM_ADMIN", "CLIENT_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required to view user attendance."
        )
    
    filters = AttendanceFilterParams(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
    )

    return AttendanceService.get_all_attendance(
        db=db,
        current_user=current_user,
        page=page,
        size=size,
        filters=filters,
    )


@router.get(
    "/summary/today",
    response_model=AttendanceSummaryResponse,
    summary="Get today's summary",
    description="Get summary statistics for today's attendance (Admin only).",
)
def get_today_summary(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Get summary statistics for today's attendance.
    
    **Admin Only** - Requires PLATFORM_ADMIN or CLIENT_ADMIN role.
    
    Returns count of total employees, present, late, half-day, absent,
    and overall attendance percentage.
    """
    # Check admin permissions
    if current_user.get("role") not in ["PLATFORM_ADMIN", "CLIENT_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required to view summary."
        )
    
    dashboard = AttendanceService.get_attendance_dashboard(
        db=db,
        current_user=current_user,
    )
    return dashboard.today_summary