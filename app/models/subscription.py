from sqlalchemy import Column
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

    plan_id = Column(
        String(36),
        ForeignKey("subscription_plans.id"),
        nullable=False
    )

    status = Column(
        String(50),
        nullable=False,
        default="active"
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

    billing_cycle = Column(
        String(20),
        nullable=False,
        default="monthly"
    )

    starts_at = Column(
        Date,
        nullable=False
    )

    ends_at = Column(
        Date,
        nullable=True
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