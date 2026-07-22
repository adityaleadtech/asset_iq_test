import uuid

from sqlalchemy import (
    Column,
    String,
    Text,
    Date,
    DateTime,
    Boolean,
    Integer,
    Enum,
    ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.config.database import Base


class AuditPlan(Base):
    __tablename__ = "audit_plans"

    id = Column(
    String(36),
    primary_key=True,
    default=lambda: str(uuid.uuid4())
)

    client_id = Column(
        String(36),
        ForeignKey("clients.id"),
        nullable=False
    )

    name = Column(String(255), nullable=False)

    description = Column(Text)

    auditor_id = Column(
        String(36),
        ForeignKey("users.id"),
        nullable=False
    )

    frequency_unit = Column(
        Enum(
            "DAY",
            "WEEK",
            "MONTH",
            name="audit_frequency_unit"
        ),
        nullable=False
    )

    frequency_interval = Column(
        Integer,
        nullable=False
    )

    start_date = Column(
        Date,
        nullable=False
    )

    end_date = Column(Date)

    next_run_date = Column(
        Date,
        nullable=False
    )

    status = Column(
        Enum(
            "ACTIVE",
            "PAUSED",
            "COMPLETED",
            "CANCELLED",
            name="audit_plan_status"
        ),
        default="ACTIVE",
        nullable=False
    )

    created_by = Column(
        String(36),
        ForeignKey("users.id"),
        nullable=False
    )

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

    # Relationships
    targets = relationship(
        "AuditTarget",
        back_populates="audit_plan",
        cascade="all, delete-orphan"
    )

    sessions = relationship(
        "AuditSession",
        back_populates="audit_plan",
        cascade="all, delete-orphan"
    )
    client = relationship("Client")

    auditor = relationship(
    "User",
    foreign_keys=[auditor_id]
)   

    creator = relationship(
    "User",
    foreign_keys=[created_by]
)