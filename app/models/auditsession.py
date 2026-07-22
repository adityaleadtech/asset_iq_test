import uuid

from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship
from app.config.database import Base


class AuditSession(Base):
    __tablename__ = "audit_sessions"

    id = Column(
    String(36),
    primary_key=True,
    default=lambda: str(uuid.uuid4())
)

    audit_plan_id = Column(
        String(36),
        ForeignKey("audit_plans.id", ondelete="CASCADE"),
        nullable=False
    )

    scheduled_date = Column(
        Date,
        nullable=False
    )

    started_at = Column(DateTime)

    completed_at = Column(DateTime)

    status = Column(
        Enum(
            "PENDING",
            "IN_PROGRESS",
            "COMPLETED",
            "OVERDUE",
            "CANCELLED",
            name="audit_session_status"
        ),
        default="PENDING",
        nullable=False
    )

    total_assets = Column(
        Integer,
        default=0
    )

    audited_assets = Column(
        Integer,
        default=0
    )

    conducted_by = Column(
        String(36),
        ForeignKey("users.id")
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )
    assigned_to = Column(
    String(36),
    ForeignKey("users.id"),
    nullable=False
)

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )

    audit_plan = relationship(
        "AuditPlan",
        back_populates="sessions"
    )

    results = relationship(
        "AuditResult",
        back_populates="audit_session",
        cascade="all, delete-orphan"
    )
    conductor = relationship(
    "User",
    foreign_keys=[conducted_by]
)
    assigned_user = relationship(
    "User",
    foreign_keys=[assigned_to]
)