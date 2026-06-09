from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import func

from datetime import datetime
from app.config.database import Base


class PlatformAdmin(Base):
    __tablename__ = "platform_admins"

    id = Column(String(36), primary_key=True)

    email = Column(String(255), unique=True, nullable=False)

    password_hash = Column(String(255), nullable=False)

    full_name = Column(String(255), nullable=False)

    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(
    DateTime,
    nullable=False,
    server_default=func.now()
)
    
    updated_at = Column(
    DateTime,
    nullable=True,
    onupdate=func.now()
)

    role = Column(String(50), nullable=False)