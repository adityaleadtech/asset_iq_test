from sqlalchemy import Column, String, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.config.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    client_id = Column(String(36), ForeignKey("clients.id"), nullable=True)
    subscription_id = Column(String(36), nullable=True)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=True)
    
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    role = Column(String(50), nullable=False)
    employee_id = Column(String(100), nullable=True)
    profile_photo_url = Column(Text, nullable=True)
    custom_role_id = Column(String(36), nullable=True)
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    last_login = Column(DateTime, nullable=True)

    
    # Relationships
    client = relationship("Client", back_populates="users")
    attendance_records = relationship(
    "Attendance",
    back_populates="user"
)
    
    department = relationship(
        "Department",
        foreign_keys=[department_id],
        back_populates="users"
    )
    
    managed_departments = relationship(
        "Department",
        foreign_keys="Department.manager_id",
        back_populates="manager"
    )
    
    # Asset relationships
    assigned_assets = relationship(
        "Asset",
        foreign_keys="Asset.assigned_to_user_id",
        back_populates="assigned_to_user"
    )
    
    created_assets = relationship(
        "Asset",
        foreign_keys="Asset.created_by",
        back_populates="created_by_user"
    )
    raised_maintenance_tasks = relationship(
    "MaintenanceTask",
    foreign_keys="[MaintenanceTask.raised_by]"
)

    approved_maintenance_tasks = relationship(
    "MaintenanceTask",
    foreign_keys="[MaintenanceTask.approved_by]"
)
    
    scanned_assets = relationship(
        "Asset",
        foreign_keys="Asset.last_scanned_by",
        back_populates="scanned_by_user"
    )
    
    # Scan log relationships - REMOVED DUPLICATE
    scan_logs = relationship(
        "AssetScanLog",
        foreign_keys="AssetScanLog.scanned_by",
        back_populates="scanner"
    )

    password_reset_token = Column(
    String(255),
    nullable=True
)

    password_reset_expires_at = Column(
    DateTime,
    nullable=True
)