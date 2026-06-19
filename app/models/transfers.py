from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import Float
from datetime import datetime

from app.config.database import Base


class Transfer(Base):

    __tablename__ = "transfers"

    id = Column(
        String(36),
        primary_key=True
    )

    asset_id = Column(
        String(36),
        nullable=False
    )

    from_client_id = Column(
        String(36)
    )

    to_client_id = Column(
        String(36)
    )

    from_location_id = Column(
        String(36)
    )

    to_location_id = Column(
        String(36)
    )

    # Add these columns in DB
    from_user_id = Column(
        String(36)
    )

    to_user_id = Column(
        String(36)
    )

    dispatched_by = Column(
        String(36),
        nullable=False
    )

    received_by = Column(
        String(36)
    )

    driver_id = Column(
        String(36)
    )

    status = Column(
        String(50),
        default="DISPATCHED"
    )

    dispatch_latitude = Column(
        Float
    )

    dispatch_longitude = Column(
        Float
    )

    receive_latitude = Column(
        Float
    )

    receive_longitude = Column(
        Float
    )

    receiver_signature_url = Column(
        Text
    )

    photos_urls = Column(
        Text
    )

    notes = Column(
        Text
    )

    requires_approval = Column(
        Boolean,
        default=False
    )

    approved_by = Column(
        String(36)
    )

    approved_at = Column(
        DateTime
    )

    dispatched_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    received_at = Column(
        DateTime
    )

    due_by = Column(
        DateTime
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )