# app/models/asset.py - Updated with correct transfer relationship

from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Float,
    Text,
    ForeignKey,
    Date,
    Numeric,
    Integer,
    JSON,
)
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.config.database import Base


class Asset(Base):
    __tablename__ = "assets"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    client_id = Column(
        CHAR(36),
        ForeignKey("clients.id"),
        nullable=False
    )

    # Business Location (Not GPS)
    location_id = Column(
        CHAR(36),
        ForeignKey("locations.id"),
        nullable=True
    )

    # Foreign Keys
    category_id = Column(
        CHAR(36),
        ForeignKey("asset_categories.id"),
        nullable=True
    )

    type_id = Column(
        CHAR(36),
        ForeignKey("asset_types.id"),
        nullable=True
    )

    parent_asset_id = Column(
        CHAR(36),
        ForeignKey("assets.id"),
        nullable=True
    )

    department_id = Column(
        CHAR(36),
        ForeignKey("departments.id"),
        nullable=True
    )

    assigned_to_user_id = Column(
        CHAR(36),
        ForeignKey("users.id"),
        nullable=True
    )

    created_by = Column(
        CHAR(36),
        ForeignKey("users.id"),
        nullable=True
    )

    # Basic Information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    serial_number = Column(String(255), nullable=True)
    model = Column(String(255), nullable=True)
    manufacturer = Column(String(255), nullable=True)

    # Purchase Information
    purchase_date = Column(Date, nullable=True)
    purchase_value = Column(Numeric(15, 2), nullable=True)

    # Asset Status
    asset_condition = Column(
        String(50),
        nullable=False,
        default="ACTIVE"
    )

    tag_state = Column(
        String(50),
        nullable=False,
        default="NOT_TAGGED"
    )

    # Current GPS
    current_latitude = Column(Float, nullable=True)
    current_longitude = Column(Float, nullable=True)

    # Tracking
    is_tracking = Column(
        Boolean,
        nullable=False,
        default=False
    )

    current_tracking_session_id = Column(
        CHAR(36),
        ForeignKey("tracking_sessions.id"),
        nullable=True
    )

    # Last Scan
    last_scanned_by = Column(
        CHAR(36),
        ForeignKey("users.id"),
        nullable=True
    )

    last_scanned_at = Column(
        DateTime,
        nullable=True
    )

    # QR & Images
    qr_code_url = Column(String(500), nullable=True)
    created_image_url = Column(String(500), nullable=True)
    latest_image_url = Column(String(500), nullable=True)
    barcode_url = Column(Text, nullable=True)

    # Additional Data
    remarks = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)
    custom_fields = Column(JSON, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # ============================================================
    # RELATIONSHIPS
    # ============================================================

    client = relationship("Client", back_populates="assets")
    location = relationship("Location", back_populates="assets")
    category = relationship("AssetCategory", back_populates="assets")
    asset_type = relationship("AssetType", back_populates="assets")
    department = relationship("Department", back_populates="assets")

    assigned_to_user = relationship(
        "User",
        foreign_keys=[assigned_to_user_id],
        back_populates="assigned_assets"
    )

    created_by_user = relationship(
        "User",
        foreign_keys=[created_by],
        back_populates="created_assets"
    )

    scanned_by_user = relationship(
        "User",
        foreign_keys=[last_scanned_by],
        back_populates="scanned_assets"
    )

    parent_asset = relationship(
        "Asset",
        remote_side=[id],
        backref="children"
    )

    # ✅ FIXED: Use transfer_assets instead of transfers
    transfer_assets = relationship(
        "TransferAsset",
        back_populates="asset",
        cascade="all, delete-orphan"
    )

    scan_logs = relationship(
        "AssetScanLog",
        back_populates="asset",
        cascade="all, delete-orphan"
    )

    maintenance_tasks = relationship(
        "MaintenanceTask",
        back_populates="asset",
        cascade="all, delete-orphan"
    )


class AssetScanLog(Base):
    """
    Track all QR code scans for an asset with historical condition tracking.
    """

    __tablename__ = "asset_scan_logs"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    asset_id = Column(CHAR(36), ForeignKey("assets.id"), nullable=False)

    scanned_by = Column(CHAR(36), ForeignKey("users.id"), nullable=False)

    # GPS Location
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Scan Image
    image_url = Column(String(500), nullable=True)

    remarks = Column(Text, nullable=True)

    # Historical State
    asset_condition = Column(String(50), nullable=True)
    tag_state = Column(String(50), nullable=True)

    verification_type = Column(String(50), nullable=True)

    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)

    scan_number = Column(Integer, nullable=True)

    scanned_at = Column(DateTime, server_default=func.now())
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    asset = relationship("Asset", back_populates="scan_logs")
    scanner = relationship("User", foreign_keys=[scanned_by])