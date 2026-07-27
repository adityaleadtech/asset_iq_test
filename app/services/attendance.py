from datetime import datetime, date, timedelta
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.attendance import Attendance, AttendanceStatus
from app.models.office_timing import OfficeTiming
from app.models.users import User
# ❌ Remove Location import - no longer needed
# from app.models.location import Location

from app.schemas.attendance import (
    AttendanceCheckIn,
    AttendanceCheckOut,
    AttendanceResponse,
    AttendanceHistoryResponse,
    AttendanceSummaryResponse,
    AttendanceDashboardResponse,
    AttendanceFilterParams,
)


class AttendanceService:

    @staticmethod
    def check_in(
        payload: AttendanceCheckIn,
        db: Session,
        current_user: dict,
    ) -> AttendanceResponse:
        """
        Record employee check-in.
        
        Flow:
        1. Validate user role (USER or MANAGER)
        2. Check if already checked in today
        3. Get user's office timing via office_timing_id (NEW)
        4. Determine status based on check-in time
        5. Create attendance record
        6. Return response
        """
        
        # Step 1: Validate role
        role = current_user.get("role")
        
        if role not in ["USER", "MANAGER"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only employees can check in."
            )
        
        # Step 2: Today's date
        today = date.today()
        
        # Step 3: Check if already checked in today
        existing = (
            db.query(Attendance)
            .filter(
                Attendance.user_id == current_user["id"],
                Attendance.attendance_date == today,
            )
            .first()
        )
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already checked in today."
            )
        
        # Step 4: Get User (NO Location join)
        user = (
            db.query(User)
            .filter(User.id == current_user["id"])
            .first()
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )
        
        # Step 5: Check if user has an office timing assigned
        if not user.office_timing_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not assigned to an office timing. Please contact your administrator."
            )
        
        # Step 6: Get Office Timing directly
        office_timing = (
            db.query(OfficeTiming)
            .filter(
                OfficeTiming.id == user.office_timing_id,
                OfficeTiming.is_active == True,
            )
            .first()
        )
        
        if not office_timing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Office timing not found or inactive."
            )
        
        # Step 7: Current time
        now = datetime.now()
        
        # Step 8: Calculate status
        scheduled = datetime.combine(
            today,
            office_timing.check_in_time,
        )
        
        minutes_late = int(
            (now - scheduled).total_seconds() / 60
        )
        
        # Determine status based on lateness
        if minutes_late <= office_timing.late_after_minutes:
            attendance_status = AttendanceStatus.PRESENT
        elif minutes_late <= office_timing.half_day_after_minutes:
            attendance_status = AttendanceStatus.LATE
        else:
            attendance_status = AttendanceStatus.HALF_DAY
        
        # Step 9: Create attendance record
        attendance = Attendance(
            client_id=user.client_id,
            user_id=user.id,
            office_timing_id=office_timing.id,
            attendance_date=today,
            check_in=now,
            check_in_latitude=payload.latitude,
            check_in_longitude=payload.longitude,
            status=attendance_status,
            working_minutes=0,
            is_late=(attendance_status in [AttendanceStatus.LATE, AttendanceStatus.HALF_DAY]),
            is_half_day=(attendance_status == AttendanceStatus.HALF_DAY),
        )
        
        # Step 10: Save
        db.add(attendance)
        db.commit()
        db.refresh(attendance)
        
        # Step 11: Return response
        return AttendanceResponse(
            id=attendance.id,
            attendance_date=attendance.attendance_date,
            user_id=user.id,
            user_name=user.full_name,
            office_timing_id=office_timing.id,
            office_timing_name=office_timing.name,
            check_in=attendance.check_in,
            check_out=attendance.check_out,
            check_in_latitude=attendance.check_in_latitude,
            check_in_longitude=attendance.check_in_longitude,
            check_out_latitude=attendance.check_out_latitude,
            check_out_longitude=attendance.check_out_longitude,
            working_minutes=attendance.working_minutes,
            status=attendance.status.value,
            is_late=attendance.is_late,
            is_half_day=attendance.is_half_day,
            remarks=attendance.remarks,
            created_at=attendance.created_at,
            updated_at=attendance.updated_at,
        )

    @staticmethod
    def check_out(
        payload: AttendanceCheckOut,
        db: Session,
        current_user: dict,
    ) -> AttendanceResponse:
        """
        Record employee check-out.
        """
        
        # Step 1: Validate role
        role = current_user.get("role")
        
        if role not in ["USER", "MANAGER"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only employees can check out."
            )
        
        # Step 2: Today's date
        today = date.today()
        
        # Step 3: Find today's attendance record
        attendance = (
            db.query(Attendance)
            .filter(
                Attendance.user_id == current_user["id"],
                Attendance.attendance_date == today,
            )
            .first()
        )
        
        if not attendance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No check-in record found for today."
            )
        
        # Step 4: Check if already checked out
        if attendance.check_out:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already checked out today."
            )
        
        # Step 5: Update check-out
        now = datetime.now()
        attendance.check_out = now
        attendance.check_out_latitude = payload.latitude
        attendance.check_out_longitude = payload.longitude
        
        # Step 6: Calculate working minutes
        if attendance.check_in:
            working_minutes = int(
                (now - attendance.check_in).total_seconds() / 60
            )
            attendance.working_minutes = working_minutes
        
        # Step 7: Update status if checked out early
        office_timing = (
            db.query(OfficeTiming)
            .filter(OfficeTiming.id == attendance.office_timing_id)
            .first()
        )
        
        if office_timing and attendance.check_in:
            scheduled_check_in = datetime.combine(
                today,
                office_timing.check_in_time,
            )
            scheduled_check_out = datetime.combine(
                today,
                office_timing.check_out_time,
            )
            
            hours_worked = attendance.working_minutes / 60
            expected_hours = (scheduled_check_out - scheduled_check_in).total_seconds() / 3600
            
            if hours_worked < expected_hours / 2:
                attendance.status = AttendanceStatus.HALF_DAY
                attendance.is_half_day = True
        
        # Step 8: Save
        db.commit()
        db.refresh(attendance)
        
        # Step 9: Load user for response
        user = (
            db.query(User)
            .filter(User.id == current_user["id"])
            .first()
        )
        
        # Step 10: Return response
        return AttendanceResponse(
            id=attendance.id,
            attendance_date=attendance.attendance_date,
            user_id=user.id,
            user_name=user.full_name,
            office_timing_id=attendance.office_timing_id,
            office_timing_name=office_timing.name if office_timing else None,
            check_in=attendance.check_in,
            check_out=attendance.check_out,
            check_in_latitude=attendance.check_in_latitude,
            check_in_longitude=attendance.check_in_longitude,
            check_out_latitude=attendance.check_out_latitude,
            check_out_longitude=attendance.check_out_longitude,
            working_minutes=attendance.working_minutes,
            status=attendance.status.value,
            is_late=attendance.is_late,
            is_half_day=attendance.is_half_day,
            remarks=attendance.remarks,
            created_at=attendance.created_at,
            updated_at=attendance.updated_at,
        )

    @staticmethod
    def get_my_attendance(
        db: Session,
        current_user: dict,
    ) -> AttendanceResponse:
        """
        Get today's attendance record for the current user.
        """
        
        today = date.today()
        
        attendance = (
            db.query(Attendance)
            .filter(
                Attendance.user_id == current_user["id"],
                Attendance.attendance_date == today,
            )
            .first()
        )
        
        if not attendance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No attendance record found for today."
            )
        
        user = (
            db.query(User)
            .filter(User.id == current_user["id"])
            .first()
        )
        
        office_timing = (
            db.query(OfficeTiming)
            .filter(OfficeTiming.id == attendance.office_timing_id)
            .first()
        )
        
        return AttendanceResponse(
            id=attendance.id,
            attendance_date=attendance.attendance_date,
            user_id=user.id,
            user_name=user.full_name,
            office_timing_id=attendance.office_timing_id,
            office_timing_name=office_timing.name if office_timing else None,
            check_in=attendance.check_in,
            check_out=attendance.check_out,
            check_in_latitude=attendance.check_in_latitude,
            check_in_longitude=attendance.check_in_longitude,
            check_out_latitude=attendance.check_out_latitude,
            check_out_longitude=attendance.check_out_longitude,
            working_minutes=attendance.working_minutes,
            status=attendance.status.value,
            is_late=attendance.is_late,
            is_half_day=attendance.is_half_day,
            remarks=attendance.remarks,
            created_at=attendance.created_at,
            updated_at=attendance.updated_at,
        )

    @staticmethod
    def get_my_attendance_history(
        db: Session,
        current_user: dict,
        page: int = 1,
        size: int = 10,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> AttendanceHistoryResponse:
        """
        Get attendance history for the current user with pagination.
        """
        
        query = db.query(Attendance).filter(
            Attendance.user_id == current_user["id"]
        )
        
        if start_date:
            query = query.filter(Attendance.attendance_date >= start_date)
        if end_date:
            query = query.filter(Attendance.attendance_date <= end_date)
        
        total = query.count()
        
        attendances = (
            query.order_by(Attendance.attendance_date.desc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )
        
        items = []
        user = (
            db.query(User)
            .filter(User.id == current_user["id"])
            .first()
        )
        
        for attendance in attendances:
            office_timing = (
                db.query(OfficeTiming)
                .filter(OfficeTiming.id == attendance.office_timing_id)
                .first()
            )
            
            items.append(
                AttendanceResponse(
                    id=attendance.id,
                    attendance_date=attendance.attendance_date,
                    user_id=user.id,
                    user_name=user.full_name,
                    office_timing_id=attendance.office_timing_id,
                    office_timing_name=office_timing.name if office_timing else None,
                    check_in=attendance.check_in,
                    check_out=attendance.check_out,
                    check_in_latitude=attendance.check_in_latitude,
                    check_in_longitude=attendance.check_in_longitude,
                    check_out_latitude=attendance.check_out_latitude,
                    check_out_longitude=attendance.check_out_longitude,
                    working_minutes=attendance.working_minutes,
                    status=attendance.status.value,
                    is_late=attendance.is_late,
                    is_half_day=attendance.is_half_day,
                    remarks=attendance.remarks,
                    created_at=attendance.created_at,
                    updated_at=attendance.updated_at,
                )
            )
        
        return AttendanceHistoryResponse(
            items=items,
            total=total,
            page=page,
            size=size,
        )

    @staticmethod
    def get_all_attendance(
        db: Session,
        current_user: dict,
        page: int = 1,
        size: int = 10,
        filters: Optional[AttendanceFilterParams] = None,
    ) -> AttendanceHistoryResponse:
        """
        Get all attendance records (Admin only).
        """
        
        role = current_user.get("role")
        if role not in ["PLATFORM_ADMIN", "CLIENT_ADMIN"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can view all attendance records."
            )
        
        query = db.query(Attendance).join(User)
        
        if role == "CLIENT_ADMIN":
            query = query.filter(
                User.client_id == current_user["client_id"]
            )
        
        if filters:
            if filters.user_id:
                query = query.filter(Attendance.user_id == filters.user_id)
            if filters.start_date:
                query = query.filter(Attendance.attendance_date >= filters.start_date)
            if filters.end_date:
                query = query.filter(Attendance.attendance_date <= filters.end_date)
            if filters.status:
                query = query.filter(Attendance.status == filters.status)
            if filters.department_id:
                query = query.filter(User.department_id == filters.department_id)
            # ❌ REMOVE location_id filter - no longer exists
            # if filters.location_id:
            #     query = query.filter(User.location_id == filters.location_id)
        
        total = query.count()
        
        attendances = (
            query.order_by(Attendance.attendance_date.desc(), Attendance.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )
        
        items = []
        
        for attendance in attendances:
            user = attendance.user
            
            office_timing = (
                db.query(OfficeTiming)
                .filter(OfficeTiming.id == attendance.office_timing_id)
                .first()
            )
            
            items.append(
                AttendanceResponse(
                    id=attendance.id,
                    attendance_date=attendance.attendance_date,
                    user_id=user.id,
                    user_name=user.full_name,
                    office_timing_id=attendance.office_timing_id,
                    office_timing_name=office_timing.name if office_timing else None,
                    check_in=attendance.check_in,
                    check_out=attendance.check_out,
                    check_in_latitude=attendance.check_in_latitude,
                    check_in_longitude=attendance.check_in_longitude,
                    check_out_latitude=attendance.check_out_latitude,
                    check_out_longitude=attendance.check_out_longitude,
                    working_minutes=attendance.working_minutes,
                    status=attendance.status.value,
                    is_late=attendance.is_late,
                    is_half_day=attendance.is_half_day,
                    remarks=attendance.remarks,
                    created_at=attendance.created_at,
                    updated_at=attendance.updated_at,
                )
            )
        
        return AttendanceHistoryResponse(
            items=items,
            total=total,
            page=page,
            size=size,
        )

    @staticmethod
    def get_attendance_dashboard(
        db: Session,
        current_user: dict,
    ) -> AttendanceDashboardResponse:
        """
        Get attendance dashboard statistics (Admin only).
        """
        
        role = current_user.get("role")
        if role not in ["PLATFORM_ADMIN", "CLIENT_ADMIN"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can view the attendance dashboard."
            )
        
        today = date.today()
        
        # Get all users for the client
        user_query = db.query(User)
        if role == "CLIENT_ADMIN":
            user_query = user_query.filter(User.client_id == current_user["client_id"])
        
        total_employees = user_query.count()
        
        # Get today's attendance
        today_attendance = (
            db.query(Attendance)
            .join(User)
            .filter(Attendance.attendance_date == today)
        )
        
        if role == "CLIENT_ADMIN":
            today_attendance = today_attendance.filter(
                User.client_id == current_user["client_id"]
            )
        
        # Count by status
        present_today = today_attendance.filter(
            Attendance.status == AttendanceStatus.PRESENT
        ).count()
        
        late_today = today_attendance.filter(
            Attendance.status == AttendanceStatus.LATE
        ).count()
        
        half_day_today = today_attendance.filter(
            Attendance.status == AttendanceStatus.HALF_DAY
        ).count()
        
        checked_in_today = today_attendance.count()
        absent_today = total_employees - checked_in_today
        
        # Calculate overall attendance percentage (last 30 days)
        thirty_days_ago = today - timedelta(days=30)
        
        total_working_days = (
            db.query(func.count(Attendance.id))
            .join(User)
            .filter(
                Attendance.attendance_date >= thirty_days_ago,
                Attendance.attendance_date <= today,
                Attendance.status.in_([
                    AttendanceStatus.PRESENT,
                    AttendanceStatus.LATE,
                    AttendanceStatus.HALF_DAY,
                ])
            )
        )
        
        if role == "CLIENT_ADMIN":
            total_working_days = total_working_days.filter(
                User.client_id == current_user["client_id"]
            )
        
        total_working_days_count = total_working_days.scalar() or 0
        
        total_possible_days = total_employees * 30
        overall_attendance_percentage = (
            round((total_working_days_count / total_possible_days) * 100, 2)
            if total_possible_days > 0
            else 0
        )
        
        # Weekly attendance (last 7 days)
        weekly_attendance = []
        for i in range(7):
            day = today - timedelta(days=i)
            day_attendance = (
                db.query(Attendance)
                .join(User)
                .filter(Attendance.attendance_date == day)
            )
            
            if role == "CLIENT_ADMIN":
                day_attendance = day_attendance.filter(
                    User.client_id == current_user["client_id"]
                )
            
            present_count = day_attendance.filter(
                Attendance.status.in_([
                    AttendanceStatus.PRESENT,
                    AttendanceStatus.LATE,
                ])
            ).count()
            
            absent_count = total_employees - day_attendance.count()
            
            weekly_attendance.append({
                "date": day.isoformat(),
                "present": present_count,
                "absent": absent_count,
            })
        
        # Monthly attendance (by week)
        monthly_attendance = []
        for week in range(4):
            week_start = today - timedelta(days=(week * 7) + 7)
            week_end = today - timedelta(days=week * 7)
            
            week_attendance = (
                db.query(Attendance)
                .join(User)
                .filter(
                    Attendance.attendance_date >= week_start,
                    Attendance.attendance_date <= week_end,
                    Attendance.status.in_([
                        AttendanceStatus.PRESENT,
                        AttendanceStatus.LATE,
                    ])
                )
            )
            
            if role == "CLIENT_ADMIN":
                week_attendance = week_attendance.filter(
                    User.client_id == current_user["client_id"]
                )
            
            present_count = week_attendance.count()
            
            monthly_attendance.append({
                "week": f"Week {4 - week}",
                "present": present_count,
                "absent": (total_employees * 7) - present_count,
            })
        
        # Build summary
        summary = AttendanceSummaryResponse(
            total_employees=total_employees,
            present_today=present_today,
            late_today=late_today,
            absent_today=absent_today,
            half_day_today=half_day_today,
            overall_attendance_percentage=overall_attendance_percentage,
        )
        
        return AttendanceDashboardResponse(
            today_summary=summary,
            weekly_attendance=weekly_attendance,
            monthly_attendance=monthly_attendance,
        )