import uuid

from sqlalchemy import (
    Column,
    String,
    DateTime,
    DECIMAL,
    ForeignKey,
)

from sqlalchemy.orm import relationship

from sqlalchemy.sql import func

from app.config.database import Base


class GPSLog(Base):
    __tablename__ = "gps_logs"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    tracking_session_id = Column(
        String(36),
        ForeignKey("tracking_sessions.id"),
        nullable=False
    )

    asset_id = Column(
        String(36),
        ForeignKey("assets.id"),
        nullable=False
    )

    latitude = Column(
        DECIMAL(10, 7),
        nullable=False
    )

    longitude = Column(
        DECIMAL(10, 7),
        nullable=False
    )

    accuracy = Column(
        DECIMAL(6, 2),
        nullable=True
    )

    speed = Column(
        DECIMAL(6, 2),
        nullable=True
    )

    recorded_at = Column(
        DateTime(timezone=True),
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    tracking_session = relationship(
        "TrackingSession",
        back_populates="gps_logs"
    )

    asset = relationship("Asset")