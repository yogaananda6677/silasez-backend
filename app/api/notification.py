from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.dependencies import get_db
from app.crud import notification as notification_crud
from app.models.user import User
from app.schemas.notification import NotificationSummaryResponse


router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=NotificationSummaryResponse)
def list_notifications(
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {
        "unread_count": notification_crud.unread_count(db, current_user.id),
        "notifications": notification_crud.list_for_user(db, current_user.id, limit),
    }


@router.patch("/{notification_id}/read", status_code=204)
def mark_notification_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not notification_crud.mark_read(db, current_user.id, notification_id):
        raise HTTPException(status_code=404, detail="Notifikasi tidak ditemukan.")


@router.patch("/read-all", status_code=204)
def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notification_crud.mark_all_read(db, current_user.id)
