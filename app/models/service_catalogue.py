from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy.sql import func

from app.config.database import Base



class ServiceCatalogue(Base):

    __tablename__ = "service_catalogue"

    id = Column(
        String(36),
        primary_key=True
    )

    code = Column(
        String(100),
        unique=True,
        nullable=False
    )

    name = Column(
        String(255),
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