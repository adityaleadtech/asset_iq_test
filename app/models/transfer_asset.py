import uuid

from sqlalchemy import Column, ForeignKey, DateTime
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.config.database import Base


class TransferAsset(Base):
    __tablename__ = "transfer_assets"

    id = Column(
        CHAR(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    transfer_id = Column(
        CHAR(36),
        ForeignKey("transfers.id", ondelete="CASCADE"),
        nullable=False
    )

    asset_id = Column(
        CHAR(36),
        ForeignKey("assets.id"),
        nullable=False
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

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    transfer = relationship(
        "Transfer",
        back_populates="assets"
    )