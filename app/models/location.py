import uuid

from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Float,
    Integer,
    Text,
    ForeignKey,
    Enum,
    CHAR
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.config.database import Base
from app.enums.location_type import (
    LocationType
)


class Location(Base):
    __tablename__ = "locations"

    #
    # Primary Key
    #
    id = Column(
        CHAR(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    #
    # Ownership
    #
    client_id = Column(
        CHAR(36),
        ForeignKey("clients.id"),
        nullable=False,
        index=True
    )

    #
    # Self Reference
    #
    parent_location_id = Column(
        CHAR(36),
        ForeignKey("locations.id"),
        nullable=True,
        index=True
    )

    #
    # Name
    #
    name = Column(
        String(255),
        nullable=False
    )

    #
    # Used for:
    # India
    # INDIA
    # indIA
    #
    normalized_name = Column(
        String(255),
        nullable=False,
        index=True
    )

    #
    # Hierarchy Type
    #
    location_type = Column(
        Enum(LocationType),
        nullable=False,
        index=True
    )

    #
    # Optional Code
    #
    code = Column(
        String(50),
        nullable=True
    )

    #
    # Optional Metadata
    #
    postal_code = Column(
        String(20),
        nullable=True
    )

    latitude = Column(
        Float,
        nullable=True
    )

    longitude = Column(
        Float,
        nullable=True
    )

    radius_meters = Column(
        Integer,
        default=200,
        nullable=False
    )

    description = Column(
        Text,
        nullable=True
    )

    #
    # Soft Delete
    #
    is_active = Column(
        Boolean,
        default=True,
        nullable=False
    )

    #
    # Audit
    #
    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )

    #
    # Relationships
    #

    client = relationship(
        "Client",
        back_populates="locations"
    )

    parent = relationship(
        "Location",
        remote_side=[id],
        back_populates="children"
    )

    children = relationship(
        "Location",
        back_populates="parent"
    )

    assets = relationship(
        "Asset",
        back_populates="location"
    )

    departments = relationship(
        "Department",
        back_populates="location"
    )