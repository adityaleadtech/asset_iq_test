from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import Text
from sqlalchemy.sql import func

from app.config.database import Base


class User(Base):

    __tablename__ = "users"

    id = Column(String(36), primary_key=True)

    client_id = Column(String(36), nullable=False)

    subscription_id = Column(String(36))

    department_id = Column(String(36))

    email = Column(String(255), nullable=False)

    password_hash = Column(String(255), nullable=False)

    full_name = Column(String(255), nullable=False)

    phone = Column(String(50))

    role = Column(String(50), nullable=False)

    employee_id = Column(String(100))

    profile_photo_url = Column(Text)

    is_active = Column(Boolean, default=True)

    last_login_at = Column(DateTime)

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )