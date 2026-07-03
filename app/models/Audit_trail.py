from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
)

from sqlalchemy.sql import func

from app.config.database import Base
from sqlalchemy.dialects.mysql import LONGTEXT


class AuditTrail(Base):
    __tablename__ = "audit_trail"

    # =====================================================
    # PRIMARY KEY
    # =====================================================

    id = Column(
        String(36),
        primary_key=True
    )

    # =====================================================
    # CLIENT
    # =====================================================

    client_id = Column(
        String(36),
        nullable=True,
        index=True
    )

    # =====================================================
    # ACTOR
    # =====================================================

    actor_type = Column(
        String(20),
        nullable=False,
        index=True
    )

    actor_id = Column(
        String(36),
        nullable=True
    )

    # =====================================================
    # ACTION
    # =====================================================

    action = Column(
        String(100),
        nullable=False
    )

    # =====================================================
    # ENTITY
    # =====================================================

    entity_type = Column(
        String(100),
        nullable=False,
        index=True
    )

    entity_id = Column(
        String(36),
        nullable=False
    )

    # =====================================================
    # CHANGES
    # =====================================================

    old_value = Column(
    LONGTEXT,
    nullable=True
)

    new_value = Column(
    LONGTEXT,
    nullable=True
)
    # =====================================================
    # REQUEST INFORMATION
    # =====================================================

    ip_address = Column(
        String(45),
        nullable=True
    )

    # =====================================================
    # TIMESTAMP
    # =====================================================

    performed_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now()
    )