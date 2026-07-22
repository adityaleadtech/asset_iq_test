import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import relationship
from app.config.database import Base


class AuditTarget(Base):
    __tablename__ = "audit_targets"

    id = Column(
    String(36),
    primary_key=True,
    default=lambda: str(uuid.uuid4())


)
    
    target_id = Column(
    String(36),
    nullable=False,
    index=True
)

    audit_plan_id = Column(
        String(36),
        ForeignKey("audit_plans.id", ondelete="CASCADE"),
        nullable=False
    )

    target_type = Column(
        Enum(
            "LOCATION",
            "DEPARTMENT",
            "CATEGORY",
            "ASSET",
            name="audit_target_type"
        ),
        nullable=False
    )

    target_id = Column(
        String(36),
        nullable=False
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    audit_plan = relationship(
        "AuditPlan",
        back_populates="targets"
    )
    audit_plan = relationship(
    "AuditPlan",
    back_populates="audit_targets"
)