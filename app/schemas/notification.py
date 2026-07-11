from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.enums import NotificationType


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    message: str
    type: NotificationType
    is_read: bool
    created_at: datetime


class NotificationSummaryResponse(BaseModel):
    unread_count: int
    notifications: list[NotificationResponse]
