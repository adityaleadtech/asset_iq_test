import uuid

from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
)
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.config.database import Base


class Transfer(Base):
    __tablename__ = "transfers"

    id = Column(
        CHAR(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    asset_id = Column(
        CHAR(36),
        ForeignKey("assets.id"),
        nullable=False
    )

    client_id = Column(
        CHAR(36),
        ForeignKey("clients.id"),
        nullable=False
    )

    from_location_id = Column(
        CHAR(36),
        ForeignKey("locations.id"),
        nullable=True
    )

    to_location_id = Column(
        CHAR(36),
        ForeignKey("locations.id"),
        nullable=True
    )

    from_department_id = Column(
        CHAR(36),
        ForeignKey("departments.id"),
        nullable=True
    )

    to_department_id = Column(
        CHAR(36),
        ForeignKey("departments.id"),
        nullable=True
    )

    from_user_id = Column(
        CHAR(36),
        ForeignKey("users.id"),
        nullable=True
    )

    to_user_id = Column(
        CHAR(36),
        ForeignKey("users.id"),
        nullable=True
    )

    transfer_type = Column(
        String(50),
        nullable=False,
        default="LOCATION"
    )

    transfer_reason = Column(
        String(255),
        nullable=True
    )

    # Keeping DB column name
    transferred_by = Column(
        "dispatched_by",
        CHAR(36),
        ForeignKey("users.id"),
        nullable=False
    )

    received_by = Column(
        CHAR(36),
        ForeignKey("users.id"),
        nullable=True
    )

    status = Column(
        String(50),
        nullable=False,
        default="COMPLETED"
    )

    receiver_signature_url = Column(
        Text,
        nullable=True
    )

    photos_urls = Column(
        Text,
        nullable=True
    )

    notes = Column(
        Text,
        nullable=True
    )

    requires_approval = Column(
        Boolean,
        default=False
    )

    approved_by = Column(
        CHAR(36),
        ForeignKey("users.id"),
        nullable=True
    )

    approved_at = Column(
        DateTime,
        nullable=True
    )

    transferred_at = Column(
        DateTime,
        server_default=func.now()
    )

    received_at = Column(
        DateTime,
        nullable=True
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    # Relationships

    asset = relationship(
        "Asset",
        back_populates="transfers"
    )

    client = relationship(
        "Client"
    )

    from_location = relationship(
        "Location",
        foreign_keys=[from_location_id]
    )

    to_location = relationship(
        "Location",
        foreign_keys=[to_location_id]
    )

    from_department = relationship(
        "Department",
        foreign_keys=[from_department_id]
    )

    to_department = relationship(
        "Department",
        foreign_keys=[to_department_id]
    )

    from_user = relationship(
        "User",
        foreign_keys=[from_user_id]
    )

    to_user = relationship(
        "User",
        foreign_keys=[to_user_id]
    )

    transferred_by_user = relationship(
        "User",
        foreign_keys=[transferred_by]
    )

    received_by_user = relationship(
        "User",
        foreign_keys=[received_by]
    )

    approved_by_user = relationship(
        "User",
        foreign_keys=[approved_by]
    )