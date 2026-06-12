from sqlalchemy import Column, String, Boolean, Text, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from app.config.database import Base

class Client(Base):
    __tablename__ = "clients"

    id = Column(String(36), primary_key=True)
    client_code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False, unique=True)  # Added unique=True
    industry = Column(String(100))
    contact_email = Column(String(255), nullable=False, unique=True)  # Added unique=True
    contact_phone = Column(String(50))  # Not unique
    address = Column(Text)
    logo_url = Column(Text)
    is_active = Column(Boolean, nullable=False, default=True)
    created_by_admin_id = Column(String(36))
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    address_line_1 = Column(String(255), nullable=False)
    address_line_2 = Column(String(255), nullable=True)
    address_line_3 = Column(String(255), nullable=True)
    
    __table_args__ = (
        UniqueConstraint('name', 'contact_email', name='unique_client_name_email'),
    )