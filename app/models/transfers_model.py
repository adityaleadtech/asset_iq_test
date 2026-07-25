# app/models/transfers_model.py

from sqlalchemy import Column, CHAR, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.config.database import Base  # ✅ FIXED: Using correct Base import
from app.enums.transfer_types import TransferType  # ✅ FIXED: Using correct enum import


class Transfer(Base):
    """
    Transfer model representing asset transfers.
    
    A transfer can be of type:
    - DEPARTMENT: Assets moved to a different department
    - LOCATION: Assets moved to a different location  
    - USER: Assets reassigned to a different user
    """
    
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

    reason = Column(String(500), nullable=True)
    remarks = Column(Text, nullable=True)

    transferred_by = Column(
        CHAR(36),
        ForeignKey("users.id"),
        nullable=False
    )

    # Timestamps
    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    # Relationships
    transferred_by_user = relationship(
        "User",
        foreign_keys=[transferred_by]
    )

    # ✅ FIXED: Use TransferAsset relationship, not direct Asset
    assets = relationship(
        "TransferAsset",
        back_populates="transfer",
        cascade="all, delete-orphan"
    )