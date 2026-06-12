from sqlalchemy import Column
from sqlalchemy import Numeric
from sqlalchemy import String
from sqlalchemy import Integer
from sqlalchemy import Date
from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy.sql import func

from app.config.database import Base


class Subscription(Base):

    __tablename__ = "subscriptions"

    id = Column(
        String(36),
        primary_key=True
    )

    client_id = Column(
        String(36),
        ForeignKey("clients.id"),
        nullable=False
    )

    status = Column(
        String(50),
        nullable=False,
        default="ACTIVE"
    )

    licence_count = Column(
        Integer,
        nullable=False
    )

    used_licences = Column(
        Integer,
        nullable=False,
        default=0
    )

    max_assets = Column(
        Integer,
        nullable=False
    )

    max_departments = Column(
        Integer,
        nullable=False
    )

    price = Column(
        Numeric(12, 2),
        nullable=False
    )

    starts_at = Column(
        Date,
        nullable=False
    )

    ends_at = Column(
        Date,
        nullable=False
    )

    auto_renew = Column(
        Boolean,
        nullable=False,
        default=True
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

