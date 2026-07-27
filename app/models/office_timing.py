# app/models/office_timing.py

import uuid

from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    Time,
    Float,
    DateTime,
    ForeignKey,
    func,
    CHAR
)

from sqlalchemy.orm import relationship

from app.config.database import Base


class OfficeTiming(Base):
    __tablename__ = "office_timings"

    id = Column(
        CHAR(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    client_id = Column(
        CHAR(36),
        ForeignKey("clients.id"),
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

    # Geofencing fields
    latitude = Column(
        Float,
        nullable=False
    )

    longitude = Column(
        Float,
        nullable=False
    )

    radius_in_meters = Column(
        Integer,
        nullable=False,
        default=100
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

    users = relationship(
        "User",
        back_populates="office_timing"
    )

    attendance_records = relationship(
        "Attendance",
        back_populates="office_timing"
    )

    def __repr__(self):
        return f"<OfficeTiming(id={self.id}, name='{self.name}', client_id={self.client_id})>"