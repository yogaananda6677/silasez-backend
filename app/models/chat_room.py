from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDMixin


class ChatRoom(
    Base,
    UUIDMixin,
    TimestampMixin,
):
    __tablename__ = "chat_rooms"

    peternak_id = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    # NULL jika room AI
    pakar_id = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )

    # Penanda room AI
    is_ai = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    title = mapped_column(
        String(150),
        nullable=True,
    )

    last_message = mapped_column(
        String(500),
        nullable=True,
    )

    last_message_at = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    is_closed = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    peternak = relationship(
        "User",
        foreign_keys=[peternak_id],
    )

    pakar = relationship(
        "User",
        foreign_keys=[pakar_id],
    )

    messages = relationship(
        "ChatMessage",
        back_populates="room",
        cascade="all, delete-orphan",
    )

    @property
    def pakar_photo_url(self) -> str | None:
        """Dipakai `ChatRoomResponse` (lihat `app/schemas/chat_room.py`)
        supaya frontend bisa nampilin foto profil pakar di daftar chat,
        bukan cuma ikon statis. Room AI (`pakar` None) otomatis null."""
        return self.pakar.photo_url if self.pakar else None