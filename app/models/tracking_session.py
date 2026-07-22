# app/models/trackingsession.py

import uuid

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Enum,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.config.database import Base


class TrackingSession(Base):
    __tablename__ = "tracking_sessions"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    client_id = Column(
        String(36),
        ForeignKey("clients.id"),
        nullable=False
    )

    started_by = Column(
        String(36),
        ForeignKey("users.id"),
        nullable=False
    )

    status = Column(
        Enum(
            "ACTIVE",
            "STOPPED",
            name="tracking_session_status"
        ),
        nullable=False,
        default="ACTIVE"
    )

    started_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    ended_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    client = relationship("Client")
    started_by_user = relationship("User")

    tracked_assets = relationship(
        "TrackingSessionAsset",
        back_populates="tracking_session",
        cascade="all, delete-orphan"
    )

    gps_logs = relationship(
        "GPSLog",
        back_populates="tracking_session",
        cascade="all, delete-orphan"
    )