from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Integer
from sqlalchemy import DECIMAL
from sqlalchemy import Text
from sqlalchemy import Boolean
from app.config.database import Base

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(
        String(36),
        primary_key=True
    )

    name = Column(
        String(100),
        nullable=False
    )

    # REMOVED: max_users column

    max_assets = Column(
        Integer,
        nullable=False
    )

    max_locations = Column(
        Integer,
        nullable=False,
        default=1
    )

    price_monthly = Column(
        DECIMAL(10, 2),
        nullable=True
    )

    price_annually = Column(
        DECIMAL(10, 2),
        nullable=True
    )

    features_json = Column(
        Text,
        nullable=True
    )
    
    is_active = Column(
        Boolean,
        nullable=False,
        default=True
    )