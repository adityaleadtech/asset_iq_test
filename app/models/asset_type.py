from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.config.database import Base


class AssetType(Base):
    __tablename__ = "asset_types"

    id = Column(String(36), primary_key=True)
    client_id = Column(String(36), ForeignKey("clients.id"), nullable=True)  # NULL = Global
    category_id = Column(String(36), ForeignKey("asset_categories.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(String(36), nullable=False)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships - ADD THESE
    client = relationship("Client", back_populates="asset_types")
    category = relationship("AssetCategory", back_populates="asset_types")
    assets = relationship("Asset", back_populates="asset_type")