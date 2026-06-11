from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy.sql import func

from app.config.database import Base


class Role(Base):

    __tablename__ = "roles"

    id = Column(
        String(36),
        primary_key=True
    )

    client_id = Column(
        String(36),
        nullable=False
    )

    name = Column(
        String(100),
        nullable=False
    )

    description = Column(
        Text,
        nullable=True
    )

    is_active = Column(
        Boolean,
        default=True
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )