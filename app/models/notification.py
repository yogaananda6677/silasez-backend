from uuid import UUID

from sqlalchemy import Boolean
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import Text

from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.enums import NotificationType
from app.models.mixins import UUIDMixin
from app.models.mixins import TimestampMixin


class Notification(
    Base,
    UUIDMixin,
    TimestampMixin,
):
    __tablename__ = "notifications"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )

    title: Mapped[str] = mapped_column(
        String(200),
    )

    message: Mapped[str] = mapped_column(
        Text,
    )

    type: Mapped[NotificationType] = mapped_column(
        Enum(
            NotificationType,
            name="notification_type",
        ),
        default=NotificationType.INFO,
    )

    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    user = relationship(
        "User",
        back_populates="notifications",
    )