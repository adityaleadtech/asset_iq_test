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
from app.enums.location_type import LocationType


class Location(Base):
    __tablename__ = "locations"

    id = Column(
        CHAR(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    client_id = Column(
        CHAR(36),
        ForeignKey("clients.id"),
        nullable=False,
        index=True
    )

    parent_location_id = Column(
        CHAR(36),
        ForeignKey("locations.id"),
        nullable=True,
        index=True
    )

    name = Column(
        String(255),
        nullable=False
    )

    location_type = Column(
        Enum(LocationType),
        nullable=False
    )

    code = Column(String(50))
    address_line_1 = Column(String(255))
    address_line_2 = Column(String(255))
    address_line_3 = Column(String(255))
    postal_code = Column(String(20))

    latitude = Column(Float)
    longitude = Column(Float)

    radius_meters = Column(
        Integer,
        default=200
    )

    description = Column(Text)

    is_active = Column(
        Boolean,
        default=True
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )


    # columns ...

    client = relationship(
        "Client",
        back_populates="locations"
    )

    parent = relationship(
        "Location",
        remote_side=[id],
        backref="children"
    )
    

    assets = relationship(
        "Asset",
        back_populates="location"
    )

    departments = relationship(
        "Department",
        back_populates="location"
    )
    
    
    