# app/models/transfer_asset.py

from sqlalchemy import Column, CHAR, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.config.database import Base


class TransferAsset(Base):
    """
    Junction table linking Transfers to Assets.
    
    This table tracks which assets are part of a transfer and stores
    the from/to state for each asset at the time of transfer.
    """
    
    __tablename__ = "transfer_assets"

    id = Column(
        CHAR(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    transfer_id = Column(
        CHAR(36),
        ForeignKey("transfers.id"),
        nullable=False
    )

    asset_id = Column(
        CHAR(36),
        ForeignKey("assets.id"),
        nullable=False
    )

    # From State (before transfer)
    from_department_id = Column(
        CHAR(36),
        ForeignKey("departments.id"),
        nullable=True
    )

    from_location_id = Column(
        CHAR(36),
        ForeignKey("locations.id"),
        nullable=True
    )

    from_user_id = Column(
        CHAR(36),
        ForeignKey("users.id"),
        nullable=True
    )

    # To State (after transfer)
    to_department_id = Column(
        CHAR(36),
        ForeignKey("departments.id"),
        nullable=True
    )

    to_location_id = Column(
        CHAR(36),
        ForeignKey("locations.id"),
        nullable=True
    )

    to_user_id = Column(
        CHAR(36),
        ForeignKey("users.id"),
        nullable=True
    )

    # Timestamps
    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    # Relationships
    transfer = relationship(
        "Transfer",
        back_populates="assets"
    )

    # ✅ ADD THIS RELATIONSHIP - links back to Asset
    asset = relationship(
        "Asset",
        back_populates="transfer_assets"
    )

    # Optional: relationships for the from/to references (for eager loading)
    from_department = relationship(
        "Department",
        foreign_keys=[from_department_id]
    )

    to_department = relationship(
        "Department",
        foreign_keys=[to_department_id]
    )

    from_location = relationship(
        "Location",
        foreign_keys=[from_location_id]
    )

    to_location = relationship(
        "Location",
        foreign_keys=[to_location_id]
    )

    from_user = relationship(
        "User",
        foreign_keys=[from_user_id]
    )

    to_user = relationship(
        "User",
        foreign_keys=[to_user_id]
    )