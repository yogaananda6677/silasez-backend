from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel

from app.core.enums import MessageType


class SendMessageRequest(BaseModel):
    message: str


class ChatMessageResponse(BaseModel):
    id: UUID

    room_id: UUID

    sender_id: Optional[UUID] = None

    message: str | None

    attachment_url: str | None

    message_type: MessageType

    is_read: bool

    created_at: datetime

    class Config:
        from_attributes = True


class ChatMessageListResponse(BaseModel):
    messages: list[ChatMessageResponse]