import uuid

from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    Time,
    DateTime,
    ForeignKey,
    func,
)

from sqlalchemy.orm import relationship

from app.config.database import Base


class OfficeTiming(Base):
    __tablename__ = "office_timings"

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

    location_id = Column(
        String(36),
        ForeignKey("locations.id"),
        nullable=False,
        index=True
    )

    name = Column(
        String(100),
        nullable=False
    )

    check_in_time = Column(
        Time,
        nullable=False
    )

    check_out_time = Column(
        Time,
        nullable=False
    )

    late_after_minutes = Column(
        Integer,
        nullable=False,
        default=15
    )

    half_day_after_minutes = Column(
        Integer,
        nullable=False,
        default=240
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True
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
        back_populates="office_timings"
    )

    location = relationship(
        "Location",
        back_populates="office_timings"
    )

    attendance_records = relationship(
        "Attendance",
        back_populates="office_timing"
    )
    attendance_records = relationship(
    "Attendance",
    back_populates="office_timing"
)