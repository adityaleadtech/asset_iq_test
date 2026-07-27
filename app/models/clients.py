from sqlalchemy import Column, String, Boolean, Text, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.config.database import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(String(36), primary_key=True)
    client_code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False, unique=True)
    industry = Column(String(100))
    contact_email = Column(String(255), nullable=False, unique=True)
    contact_phone = Column(String(50))
    address = Column(Text)
    logo_url = Column(Text)
    is_active = Column(Boolean, nullable=False, default=True)
    created_by_admin_id = Column(String(36))
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    address_line_1 = Column(String(255), nullable=False)
    address_line_2 = Column(String(255), nullable=True)
    address_line_3 = Column(String(255), nullable=True)
    
    # Relationships - All using string references
    assets = relationship("Asset", back_populates="client")
    users = relationship("User", back_populates="client")
    departments = relationship("Department", back_populates="client")
    subscriptions = relationship("Subscription", back_populates="client")
    asset_categories = relationship("AssetCategory", back_populates="client")
    asset_types = relationship("AssetType", back_populates="client")
    
    # ✅ KEEP THIS - OfficeTiming relationship (independent from Location)
    office_timings = relationship("OfficeTiming", back_populates="client")
    
    # ✅ KEEP THIS - Location relationship (independent from OfficeTiming)
    locations = relationship("Location", back_populates="client", cascade="all, delete-orphan")
    
    # ✅ KEEP THIS - Attendance relationship
    attendance_records = relationship("Attendance", back_populates="client")
    
    __table_args__ = (
        UniqueConstraint('name', 'contact_email', name='unique_client_name_email'),
    )

    def __repr__(self):
        return f"<Client(id={self.id}, name='{self.name}', client_code='{self.client_code}')>"