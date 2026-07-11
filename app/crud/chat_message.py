from uuid import UUID

from openai import chat
from sqlalchemy.orm import Session

from app.core.enums import MessageType
from app.models.chat_message import ChatMessage


class CRUDChatMessage:

    def create(
        self,
        db: Session,
        *,
        room_id: UUID,
        sender_id: UUID,
        message: str,
    ) -> ChatMessage:

        chat = ChatMessage(
            room_id=room_id,
            sender_id=sender_id,
            message=message,
            message_type=MessageType.TEXT,
        )

        db.add(chat)

        db.commit()

        db.refresh(chat)

        return chat

    def get_messages(
        self,
        db: Session,
        room_id: UUID,
    ) -> list[ChatMessage]:

        return (
            db.query(ChatMessage)
            .filter(ChatMessage.room_id == room_id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )
    def get_by_id(
        self,
        db: Session,
        message_id: UUID,
    ) -> ChatMessage | None:

        return (
            db.query(ChatMessage)
            .filter(ChatMessage.id == message_id)
            .first()
        )
    
    def count_unread(
        self,
        db: Session,
        room_id: UUID,
        user_id: UUID,
    ) -> int:

        return (
            db.query(ChatMessage)
            .filter(
                ChatMessage.room_id == room_id,
                ChatMessage.sender_id != user_id,
                ChatMessage.is_read.is_(False),
            )
            .count()
        )
    
    def get_last_message(
        self,
        db: Session,
        room_id: UUID,
    ) -> ChatMessage | None:

        return (
            db.query(ChatMessage)
            .filter(ChatMessage.room_id == room_id)
            .order_by(ChatMessage.created_at.desc())
            .first()
        )
    
    def delete(
        self,
        db: Session,
        chat: ChatMessage,
    ):

        db.delete(chat)

        db.commit()

    def mark_as_read(
        self,
        db: Session,
        room_id: UUID,
        user_id: UUID,
    ):

        (
            db.query(ChatMessage)
            .filter(
                ChatMessage.room_id == room_id,
                ChatMessage.sender_id != user_id,
                ChatMessage.is_read.is_(False),
            )
            .update(
                {
                    ChatMessage.is_read: True,
                },
                synchronize_session=False,
            )
        )

        db.commit()


chat_message = CRUDChatMessage()