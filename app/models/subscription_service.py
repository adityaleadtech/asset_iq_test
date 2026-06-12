from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import ForeignKey

from app.config.database import Base


class SubscriptionService(Base):

    __tablename__ = "subscription_services"

    id = Column(
        String(36),
        primary_key=True
    )

    subscription_id = Column(
        String(36),
        ForeignKey(
            "subscriptions.id"
        ),
        nullable=False
    )

    service_id = Column(
        String(36),
        ForeignKey(
            "service_catalogue.id"
        ),
        nullable=False
    )