from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, Field

from app.core.enums import MessageType


class SendMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)


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
