from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func

from app.config.database import Base
from sqlalchemy.orm import relationship

class AuditResult(Base):
    __tablename__ = "audit_results"

    id = Column(
    String(36),
    primary_key=True,
    default=lambda: str(uuid.uuid4())
)

    audit_session_id = Column(
        String(36),
        ForeignKey("audit_sessions.id", ondelete="CASCADE"),
        nullable=False
    )

    asset_id = Column(
        String(36),
        ForeignKey("assets.id"),
        nullable=False
    )

    status = Column(
        Enum(
            "IN_PLACE",
            "DISLOCATED",
            "LOST",
            "NOT_FOUND",
            name="audit_asset_status"
        ),
        nullable=False
    )

    condition_status = Column(
        Enum(
            "EXCELLENT",
            "GOOD",
            "FAIR",
            "DAMAGED",
            "BROKEN",
            name="audit_condition_status"
        )
    )

    quantity_expected = Column(
        Integer,
        default=1
    )

    quantity_found = Column(
        Integer,
        default=1
    )

    remarks = Column(Text)

    photo_url = Column(Text)

    expected_location_id = Column(
    String(36),
    ForeignKey("locations.id"),
    nullable=True
)

    expected_latitude = Column(Numeric(10, 8))

    expected_longitude = Column(Numeric(11, 8))

    audit_latitude = Column(Numeric(10, 8))

    audit_longitude = Column(Numeric(11, 8))

    location_status = Column(
    Enum(
        "VERIFIED",
        "NEARBY",
        "OUTSIDE_GEOFENCE",
        "LOCATION_UNKNOWN",
        name="audit_location_status"
    ),
    default="LOCATION_UNKNOWN",
    nullable=False
)
    audited_by = Column(
        String(36),
        ForeignKey("users.id"),
        nullable=False
    )

    audited_at = Column(
        DateTime,
        nullable=False
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

    audit_session = relationship(
        "AuditSession",
        back_populates="results"
    )
    asset = relationship("Asset")

    auditor = relationship(
    "User",
    foreign_keys=[audited_by]
)

    expected_location = relationship("Location")