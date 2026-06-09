from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Boolean
from sqlalchemy import Text
from sqlalchemy import DateTime
from sqlalchemy.sql import func

from app.config.database import Base

class Client(Base):
    __tablename__ ="clients"

    id=Column(String(36),primary_key=True)

    name=Column(String(255),nullable=False)

    industry= Column(String(100))

    contact_email = Column(String(255), nullable=False)

    contact_phone= Column(String(50))

    address= Column(Text)

    logo_url= Column(Text)

    is_active=Column(Boolean,nullable=False)

    created_by_admin_id=Column(String(36))

    created_at = Column(
    DateTime,
    nullable=False,
    server_default=func.now()
)

    updated_at = Column(
    DateTime,
    nullable=True,
    server_default=func.now(),
    onupdate=func.now()
)

