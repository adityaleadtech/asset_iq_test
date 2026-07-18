import uuid

from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
)

from sqlalchemy.orm import relationship

from sqlalchemy.sql import func

from app.config.database import Base


class TrackingSessionAsset(Base):
    __tablename__ = "tracking_session_assets"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    tracking_session_id = Column(
        String(36),
        ForeignKey(
            "tracking_sessions.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    asset_id = Column(
        String(36),
        ForeignKey("assets.id"),
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    tracking_session = relationship(
        "TrackingSession",
        back_populates="tracked_assets"
    )

    asset = relationship("Asset")   