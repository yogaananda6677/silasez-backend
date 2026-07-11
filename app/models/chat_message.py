from uuid import UUID

from sqlalchemy import Boolean, Enum, String
from sqlalchemy import ForeignKey
from sqlalchemy import Text

from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.enums import ChatSender
from app.models.mixins import UUIDMixin
from app.models.mixins import TimestampMixin
from app.core.enums import MessageType


class ChatMessage(
    Base,
    UUIDMixin,
    TimestampMixin,
):
    __tablename__="chat_messages"

    room_id = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("chat_rooms.id",ondelete="CASCADE")
    )

    sender_id = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id")
    )

    message_type = mapped_column(
        Enum(MessageType,name="message_type"),
        default=MessageType.TEXT
    )

    message = mapped_column(
        Text,
        nullable=True
    )

    attachment_url = mapped_column(
        String(500),
        nullable=True
    )

    is_read = mapped_column(
        Boolean,
        default=False
    )

    room = relationship(
        "ChatRoom",
        back_populates="messages"
    )

    sender = relationship("User")