from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Boolean
from sqlalchemy import Text
from sqlalchemy import DateTime
from app.config.database import Base


class User(Base):

    __tablename__ = "users"

    id = Column(String(36), primary_key=True)

    client_id = Column(String(36))

    subscription_id = Column(String(36))

    department_id = Column(String(36))

    email = Column(String(255))

    password_hash = Column(String(255))

    full_name = Column(String(255))

    phone = Column(String(50))

    role = Column(String(50))

    employee_id = Column(String(100))

    profile_photo_url = Column(Text)

    custom_role_id = Column(
        String(36),
        nullable=True
    )

    is_active = Column(
        Boolean,
        default=True
    )