import uuid

from sqlalchemy import (
    Column,
    Text,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Numeric
)
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.config.database import Base


class MaintenanceTask(Base):
    __tablename__ = "maintenance_tasks"

    id = Column(
        CHAR(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    asset_id = Column(
        CHAR(36),
        ForeignKey("assets.id"),
        nullable=False,
        index=True
    )

    client_id = Column(
        CHAR(36),
        ForeignKey("clients.id"),
        nullable=False,
        index=True
    )

    raised_by = Column(
        CHAR(36),
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    issue_description = Column(
        Text,
        nullable=False
    )

    # Store as JSON string
    photos_urls = Column(
        Text,
        nullable=True
    )

    estimated_cost = Column(
        Numeric(10, 2),
        nullable=True
    )

    is_emergency = Column(
        Boolean,
        default=False,
        nullable=False
    )

    status = Column(
        String(50),
        nullable=False,
        default="pending_approval"
    )

    approved_by = Column(
        CHAR(36),
        ForeignKey("users.id"),
        nullable=True,
        index=True
    )

    approved_at = Column(
        DateTime,
        nullable=True
    )

    started_at = Column(
        DateTime,
        nullable=True
    )

    vendor_name = Column(
        String(255),
        nullable=True
    )

    # Store as JSON string
    parts_replaced = Column(
        Text,
        nullable=True
    )

    completed_at = Column(
        DateTime,
        nullable=True
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    #
    # Relationships
    #

    asset = relationship(
        "Asset",
        back_populates="maintenance_tasks"
    )

    client = relationship(
        "Client"
    )

    raised_by_user = relationship(
        "User",
        foreign_keys=[raised_by],
        back_populates="raised_maintenance_tasks"
    )

    approved_by_user = relationship(
        "User",
        foreign_keys=[approved_by],
        back_populates="approved_maintenance_tasks"
    )