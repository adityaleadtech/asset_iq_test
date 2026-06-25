from sqlalchemy import CHAR, Column, String, Text, Boolean, DateTime, ForeignKey
from datetime import datetime
from sqlalchemy.orm import relationship

from app.config.database import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(String(36), primary_key=True)
    client_id = Column(String(36), ForeignKey("clients.id"), nullable=False)
    parent_department_id = Column(String(36), ForeignKey("departments.id"), nullable=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    manager_id = Column(String(36), ForeignKey("users.id"), nullable=True)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    client = relationship("Client", back_populates="departments")
    parent_department = relationship("Department", remote_side=[id], backref="sub_departments")
    
    # Department.manager relationship - points to User who is the manager
    manager = relationship(
        "User",
        foreign_keys=[manager_id],
        back_populates="managed_departments"  # FIXED: was "managed_department"
    )
    
    # Department.users relationship - points to Users in this department
    users = relationship(
        "User",
        foreign_keys="User.department_id",  # FIXED: removed brackets
        back_populates="department"
    )
    location_id = Column(
    CHAR(36),
    ForeignKey("locations.id"),
    nullable=True
)

    location = relationship(
    "Location",
    back_populates="departments"
)
    # Department.assets relationship
    assets = relationship("Asset", back_populates="department")

    