from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import Date
from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import Numeric
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy.sql import func

from app.config.database import Base


class Asset(Base):

    __tablename__ = "assets"

    id = Column(
        String(36),
        primary_key=True
    )

    client_id = Column(
        String(36),
        ForeignKey("clients.id"),
        nullable=False
    )



    category_id = Column(
        String(36),
        ForeignKey("asset_categories.id"),
        nullable=True
    )

    type_id = Column(
        String(36),
        ForeignKey("asset_types.id"),
        nullable=True
    )

    parent_asset_id = Column(
        String(36),
        ForeignKey("assets.id"),
        nullable=True
    )

    department_id = Column(
        String(36),
        ForeignKey("departments.id"),
        nullable=True
    )

    assigned_to_user_id = Column(
        String(36),
        ForeignKey("users.id"),
        nullable=True
    )

    created_by = Column(
        String(36),
        ForeignKey("users.id"),
        nullable=True
    )

    name = Column(
        String(255),
        nullable=False
    )

    description = Column(
        Text,
        nullable=True
    )

    serial_number = Column(
        String(255),
        nullable=True
    )

    model = Column(
        String(255),
        nullable=True
    )

    manufacturer = Column(
        String(255),
        nullable=True
    )

    purchase_date = Column(
        Date,
        nullable=True
    )

    purchase_value = Column(
        Numeric(12, 2),
        nullable=True
    )

    status = Column(
        String(50),
        nullable=False,
        default="AVAILABLE"
    )

    current_latitude = Column(
        Float,
        nullable=True
    )

    current_longitude = Column(
        Float,
        nullable=True
    )

    last_seen_at = Column(
        DateTime,
        nullable=True
    )

    metadata_json = Column(
        Text,
        nullable=True
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    updated_at = Column(
        DateTime,
        onupdate=func.now()
    )