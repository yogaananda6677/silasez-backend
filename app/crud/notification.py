from uuid import UUID

from sqlalchemy.orm import Session

from app.core.enums import NotificationType
from app.models.notification import Notification


def create(
    db: Session,
    *,
    user_id: UUID,
    title: str,
    message: str,
    notification_type: NotificationType = NotificationType.INFO,
) -> Notification:
    item = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=notification_type,
        is_read=False,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def list_for_user(db: Session, user_id: UUID, limit: int = 50) -> list[Notification]:
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .all()
    )


def unread_count(db: Session, user_id: UUID) -> int:
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read.is_(False))
        .count()
    )


def mark_read(db: Session, user_id: UUID, notification_id: UUID) -> bool:
    updated = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == user_id)
        .update({Notification.is_read: True}, synchronize_session=False)
    )
    db.commit()
    return updated > 0


def mark_all_read(db: Session, user_id: UUID) -> None:
    (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read.is_(False))
        .update({Notification.is_read: True}, synchronize_session=False)
    )
    db.commit()
