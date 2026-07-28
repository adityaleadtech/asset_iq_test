# app/models/attendance.py

import uuid
import enum

from sqlalchemy import (
    Boolean,
    Column,
    String,
    Date,
    DateTime,
    ForeignKey,
    Float,
    Integer,
    Enum,
    Text,
    func,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.config.database import Base


class AttendanceStatus(str, enum.Enum):
    PRESENT = "PRESENT"
    LATE = "LATE"
    HALF_DAY = "HALF_DAY"
    ABSENT = "ABSENT"


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    client_id = Column(
        String(36),
        ForeignKey("clients.id"),
        nullable=False,
        index=True
    )

    user_id = Column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    office_timing_id = Column(
        String(36),
        ForeignKey("office_timings.id"),
        nullable=False,
        index=True
    )

    attendance_date = Column(
        Date,
        nullable=False,
        index=True
    )

    # ===== CHECK-IN FIELDS =====
    check_in = Column(
        DateTime,
        nullable=True
    )

    check_in_latitude = Column(
        Float,
        nullable=True
    )

    check_in_longitude = Column(
        Float,
        nullable=True
    )

    check_in_accuracy = Column(
        Float,
        nullable=True
    )

    # ===== CHECK-OUT FIELDS =====
    check_out = Column(
        DateTime,
        nullable=True
    )

    check_out_latitude = Column(
        Float,
        nullable=True
    )

    check_out_longitude = Column(
        Float,
        nullable=True
    )

    check_out_accuracy = Column(
        Float,
        nullable=True
    )

    check_out_notes = Column(
        Text,
        nullable=True
    )

    # ===== STATUS & CALCULATIONS =====
    working_minutes = Column(
        Integer,
        default=0,
        nullable=False
    )

    status = Column(
        Enum(AttendanceStatus),
        nullable=False,
        default=AttendanceStatus.PRESENT
    )

    is_late = Column(
        Boolean,
        default=False,
        nullable=False
    )

    is_half_day = Column(
        Boolean,
        default=False,
        nullable=False
    )

    remarks = Column(
        Text,
        nullable=True
    )

    # ===== TIMESTAMPS =====
    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # ===== RELATIONSHIPS =====
    client = relationship("Client")
    user = relationship("User")
    office_timing = relationship("OfficeTiming")

    # ===== CONSTRAINTS =====
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "attendance_date",
            name="uq_attendance_user_date"
        ),
    )

    def __repr__(self):
        return f"<Attendance(id={self.id}, user_id={self.user_id}, date={self.attendance_date}, status={self.status})>"