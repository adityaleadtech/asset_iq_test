from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy.sql import func

from app.config.database import Base


class RoleServicePermission(Base):

    __tablename__ = "role_service_permissions"

    id = Column(
        String(36),
        primary_key=True
    )

    role_id = Column(
        String(36),
        nullable=False
    )

    service_id = Column(
        String(36),
        nullable=False
    )

    can_create = Column(
        Boolean,
        default=False
    )

    can_read = Column(
        Boolean,
        default=False
    )

    can_update = Column(
        Boolean,
        default=False
    )

    can_delete = Column(
        Boolean,
        default=False
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )