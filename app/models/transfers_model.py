import uuid

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.database import Base
from app.enums.transfer import TransferType


class Transfer(Base):
    __tablename__ = "transfers"

    id = Column(
        CHAR(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    client_id = Column(
        CHAR(36),
        ForeignKey("clients.id"),
        nullable=False
    )

    transfer_type = Column(
        Enum(TransferType),
        nullable=False
    )

    reason = Column(
        String(255),
        nullable=True
    )

    remarks = Column(
        Text,
        nullable=True
    )

    transferred_by = Column(
        CHAR(36),
        ForeignKey("users.id"),
        nullable=False
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )

    assets = relationship(
        "TransferAsset",
        back_populates="transfer",
        cascade="all, delete-orphan"
    )