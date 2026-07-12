import os
from uuid import UUID

import firebase_admin
from firebase_admin import credentials, messaging
from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud import device_token as token_crud


class FirebasePushService:
    _initialized = False

    @classmethod
    def _initialize(cls) -> bool:
        if cls._initialized:
            return True
        path = settings.FIREBASE_CREDENTIALS_PATH
        if not path or not os.path.isfile(path):
            return False
        if not firebase_admin._apps:
            firebase_admin.initialize_app(credentials.Certificate(path))
        cls._initialized = True
        return True

    @classmethod
    def send_to_user(
        cls,
        db: Session,
        user_id: UUID,
        *,
        title: str,
        body: str,
        category: str,
        notification_type: str,
    ) -> None:
        if not cls._initialize():
            return
        tokens = token_crud.list_tokens(db, user_id)
        if not tokens:
            return

        invalid: list[str] = []
        for token in tokens:
            try:
                messaging.send(
                    messaging.Message(
                        token=token,
                        notification=messaging.Notification(title=title, body=body),
                        data={
                            "category": category,
                            "type": notification_type,
                        },
                        android=messaging.AndroidConfig(priority="high"),
                    )
                )
            except (
                messaging.UnregisteredError,
                messaging.SenderIdMismatchError,
            ):
                invalid.append(token)
            except Exception as exc:
                print(f"FCM gagal mengirim notifikasi: {exc}")
        token_crud.delete_tokens(db, invalid)
