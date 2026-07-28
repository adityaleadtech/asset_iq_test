# app/services/attendance.py

from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from app.models.users import User
from app.models.attendance import Attendance, AttendanceStatus
from app.models.office_timing import OfficeTiming
from app.models.departments import Department

from app.schemas.attendance import (
    AttendanceCheckIn,
    AttendanceCheckOut,
    AttendanceResponse,
    AttendanceHistoryResponse,
    AttendanceDashboardResponse,
    AttendanceFilterParams,
    AttendanceSummaryResponse
)


class AttendanceService:
    
    # ✅ Added CLIENT_ADMIN to allowed roles
    ALLOWED_CHECKIN_ROLES = ["USER", "MANAGER", "CLIENT_ADMIN"]
    
    @staticmethod
    def _get_or_assign_office_timing(
        db: Session,
        user: User,
        client_id: str,
    ) -> Optional[OfficeTiming]:
        """
        Get the office timing for a user.
        If user doesn't have one, try to get the client's first active office timing.
        """
        # If user already has an office timing, use it
        if user.office_timing_id:
            office_timing = (
                db.query(OfficeTiming)
                .filter(
                    OfficeTiming.id == user.office_timing_id,
                    OfficeTiming.is_active == True,
                )
                .first()
            )
            if office_timing:
                return office_timing
        
        # If user doesn't have an office timing, get the client's first active one
        office_timing = (
            db.query(OfficeTiming)
            .filter(
                OfficeTiming.client_id == client_id,
                OfficeTiming.is_active == True,
            )
            .order_by(OfficeTiming.created_at.asc())
            .first()
        )
        
        # If found, assign it to the user for future use
        if office_timing and not user.office_timing_id:
            user.office_timing_id = office_timing.id
            db.commit()
            db.refresh(user)
        
        return office_timing
    
    @staticmethod
    def check_in(
        payload: AttendanceCheckIn,
        db: Session,
        current_user: dict,
    ) -> AttendanceResponse:
        """
        Record employee check-in.
        
        Allowed Roles: USER, MANAGER, CLIENT_ADMIN
        """
        
        # Step 1: Validate role
        role = current_user.get("role")
        
        if role not in AttendanceService.ALLOWED_CHECKIN_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Only employees can check in. Your role: {role}"
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
        
        if existing and existing.check_in:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already checked in today."
            )
        
        # Step 4: Get User
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
        
        # Step 5: Get or assign office timing (NEW)
        office_timing = AttendanceService._get_or_assign_office_timing(
            db=db,
            user=user,
            client_id=user.client_id,
        )
        
        # If still no office timing, raise error
        if not office_timing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No office timing configured for this client. Please contact your administrator."
            )
        
        # Step 6: Current time
        now = datetime.now()
        
        # Step 7: Calculate status
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
        
        # Determine flags
        is_late = (attendance_status in [AttendanceStatus.LATE, AttendanceStatus.HALF_DAY])
        is_half_day = (attendance_status == AttendanceStatus.HALF_DAY)
        
        # Step 8: Create attendance record
        attendance = Attendance(
            client_id=user.client_id,
            user_id=user.id,
            office_timing_id=office_timing.id,
            attendance_date=today,
            check_in=now,
            check_in_latitude=payload.latitude,
            check_in_longitude=payload.longitude,
            check_in_accuracy=getattr(payload, 'accuracy', None),
            status=attendance_status,
            working_minutes=0,
            is_late=is_late,
            is_half_day=is_half_day,
        )
        
        db.add(attendance)
        db.commit()
        db.refresh(attendance)
        
        # Step 9: Return response
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
            check_in_accuracy=attendance.check_in_accuracy,
            check_out_latitude=attendance.check_out_latitude,
            check_out_longitude=attendance.check_out_longitude,
            check_out_accuracy=attendance.check_out_accuracy,
            working_minutes=attendance.working_minutes,
            status=attendance.status.value if hasattr(attendance.status, 'value') else str(attendance.status),
            is_late=attendance.is_late,
            is_half_day=attendance.is_half_day,
            remarks=attendance.remarks,
            check_out_notes=attendance.check_out_notes,
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
        
        Allowed Roles: USER, MANAGER, CLIENT_ADMIN
        """
        
        # Step 1: Validate role
        role = current_user.get("role")
        
        if role not in AttendanceService.ALLOWED_CHECKIN_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Only employees can check out. Your role: {role}"
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
        attendance.check_out_accuracy = getattr(payload, 'accuracy', None)
        attendance.check_out_notes = getattr(payload, 'notes', None)
        
        # Step 6: Calculate working minutes
        if attendance.check_in:
            working_minutes = int(
                (now - attendance.check_in).total_seconds() / 60
            )
            attendance.working_minutes = working_minutes
        
        # Step 7: Update status if checked out early
        office_timing = None
        if attendance.office_timing_id:
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
        
        db.commit()
        db.refresh(attendance)
        
        # Step 8: Load user for response
        user = (
            db.query(User)
            .filter(User.id == current_user["id"])
            .first()
        )
        
        # Step 9: Return response
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
            check_in_accuracy=attendance.check_in_accuracy,
            check_out_latitude=attendance.check_out_latitude,
            check_out_longitude=attendance.check_out_longitude,
            check_out_accuracy=attendance.check_out_accuracy,
            working_minutes=attendance.working_minutes,
            status=attendance.status.value if hasattr(attendance.status, 'value') else str(attendance.status),
            is_late=attendance.is_late,
            is_half_day=attendance.is_half_day,
            remarks=attendance.remarks,
            check_out_notes=attendance.check_out_notes,
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
            check_in_accuracy=attendance.check_in_accuracy,
            check_out_latitude=attendance.check_out_latitude,
            check_out_longitude=attendance.check_out_longitude,
            check_out_accuracy=attendance.check_out_accuracy,
            working_minutes=attendance.working_minutes,
            status=attendance.status.value if hasattr(attendance.status, 'value') else str(attendance.status),
            is_late=attendance.is_late,
            is_half_day=attendance.is_half_day,
            remarks=attendance.remarks,
            check_out_notes=attendance.check_out_notes,
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
                    check_in_accuracy=attendance.check_in_accuracy,
                    check_out_latitude=attendance.check_out_latitude,
                    check_out_longitude=attendance.check_out_longitude,
                    check_out_accuracy=attendance.check_out_accuracy,
                    working_minutes=attendance.working_minutes,
                    status=attendance.status.value if hasattr(attendance.status, 'value') else str(attendance.status),
                    is_late=attendance.is_late,
                    is_half_day=attendance.is_half_day,
                    remarks=attendance.remarks,
                    check_out_notes=attendance.check_out_notes,
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
                    check_in_accuracy=attendance.check_in_accuracy,
                    check_out_latitude=attendance.check_out_latitude,
                    check_out_longitude=attendance.check_out_longitude,
                    check_out_accuracy=attendance.check_out_accuracy,
                    working_minutes=attendance.working_minutes,
                    status=attendance.status.value if hasattr(attendance.status, 'value') else str(attendance.status),
                    is_late=attendance.is_late,
                    is_half_day=attendance.is_half_day,
                    remarks=attendance.remarks,
                    check_out_notes=attendance.check_out_notes,
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
        user_query = db.query(User).filter(User.is_active == True)
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
        
        # Calculate overall attendance percentage
        overall_attendance_percentage = (
            round((checked_in_today / total_employees) * 100, 2)
            if total_employees > 0
            else 0
        )
        
        # Weekly attendance (last 7 days)
        weekly_attendance = []
        for i in range(6, -1, -1):
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
                "total": total_employees,
                "percentage": round((present_count / total_employees) * 100, 2) if total_employees > 0 else 0
            })
        
        # Monthly attendance (last 4 weeks)
        monthly_attendance = []
        for week in range(3, -1, -1):
            week_start = today - timedelta(days=(week * 7) + 7)
            week_end = today - timedelta(days=week * 7)
            
            week_attendance = (
                db.query(Attendance)
                .join(User)
                .filter(
                    Attendance.attendance_date >= week_start,
                    Attendance.attendance_date <= week_end,
                )
            )
            
            if role == "CLIENT_ADMIN":
                week_attendance = week_attendance.filter(
                    User.client_id == current_user["client_id"]
                )
            
            present_count = week_attendance.filter(
                Attendance.status.in_([
                    AttendanceStatus.PRESENT,
                    AttendanceStatus.LATE,
                ])
            ).count()
            
            monthly_attendance.append({
                "week": f"Week {4 - week}",
                "present": present_count,
                "absent": (total_employees * 7) - present_count,
                "total": total_employees * 7,
                "percentage": round((present_count / (total_employees * 7)) * 100, 2) if total_employees > 0 else 0
            })
        
        # Build summary
        summary = TodaySummary(
            total_employees=total_employees,
            present_today=present_today,
            late_today=late_today,
            absent_today=absent_today,
            half_day_today=half_day_today,
            on_leave_today=0,
            overall_attendance_percentage=overall_attendance_percentage,
        )
        
        return AttendanceDashboardResponse(
            today_summary=summary,
            weekly_attendance=weekly_attendance,
            monthly_attendance=monthly_attendance,
        )