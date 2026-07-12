from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.enums import NotificationCategory, NotificationType


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    message: str
    type: NotificationType
    category: NotificationCategory
    is_read: bool
    created_at: datetime


class NotificationSummaryResponse(BaseModel):
    unread_count: int
    notifications: list[NotificationResponse]


class DeviceTokenRequest(BaseModel):
    token: str
    platform: str = "android"
