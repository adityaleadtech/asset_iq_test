from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import Boolean
from sqlalchemy import DateTime
from datetime import datetime
from app.config.database import Base


class Department(Base):

    __tablename__ = "departments"

    id = Column(String(36), primary_key=True)

    client_id = Column(String(36), nullable=False)

    parent_department_id = Column(String(36))

    name = Column(String(255), nullable=False)

    code = Column(String(50))

    description = Column(Text)

    manager_id = Column(String(36))

    is_active = Column(Boolean)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)