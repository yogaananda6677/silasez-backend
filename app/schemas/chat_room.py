from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CreateChatRoomRequest(BaseModel):
    pakar_id: UUID | None = None
    is_ai: bool = False


class ChatRoomResponse(BaseModel):
    id: UUID

    peternak_id: UUID
    pakar_id: UUID | None

    title: str | None

    is_ai: bool
    is_closed: bool

    last_message: str | None
    last_message_at: datetime | None

    created_at: datetime

    # Foto profil pakar lawan bicara (null untuk room AI, atau kalau
    # pakar belum upload foto). Diambil dari properti `pakar_photo_url`
    # di model `ChatRoom` (lihat `app/models/chat_room.py`), yang
    # membaca `User.photo_url` lewat relasi `pakar`.
    pakar_photo_url: str | None = None
    peternak_photo_url: str | None = None
    peternak_name: str | None = None
    pakar_name: str | None = None
    unread_count: int = 0
    last_message_sender_id: UUID | None = None
    last_message_is_read: bool | None = None

    class Config:
        from_attributes = True


class ChatRoomListResponse(BaseModel):
    rooms: list[ChatRoomResponse]
