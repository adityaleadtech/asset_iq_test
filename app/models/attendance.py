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

    # ✅ office_timing_id is already here - good!
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

    check_in = Column(
        DateTime,
        nullable=True
    )

    check_out = Column(
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

    check_out_latitude = Column(
        Float,
        nullable=True
    )

    check_out_longitude = Column(
        Float,
        nullable=True
    )

    # ✅ NEW - GPS accuracy fields
    check_in_accuracy = Column(
        Float,
        nullable=True
    )

    check_out_accuracy = Column(
        Float,
        nullable=True
    )

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

    # ✅ NEW - track if employee was late
    is_late = Column(
        Boolean,
        default=False,
        nullable=False
    )

    # ✅ NEW - track if employee had half day
    is_half_day = Column(
        Boolean,
        default=False,
        nullable=False
    )

    remarks = Column(
        Text,
        nullable=True
    )

    # ✅ NEW - checkout notes (e.g., distance from office)
    check_out_notes = Column(
        Text,
        nullable=True
    )

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

    # Relationships
    client = relationship(
        "Client",
        back_populates="attendance_records"
    )

    user = relationship(
        "User",
        back_populates="attendance_records"
    )

    office_timing = relationship(
        "OfficeTiming",
        back_populates="attendance_records"
    )

    # Unique constraint to prevent duplicate check-ins per day
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "attendance_date",
            name="uq_attendance_user_date"
        ),
    )

    def __repr__(self):
        return f"<Attendance(id={self.id}, user_id={self.user_id}, date={self.attendance_date}, status={self.status})>"