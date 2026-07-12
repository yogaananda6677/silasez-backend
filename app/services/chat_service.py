from uuid import UUID
import asyncio
import re

from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.core.enums import NotificationCategory, NotificationType, UserRole
from app.crud import notification as notification_crud
from app.crud.chat_message import chat_message
from app.crud.chat_room import chat_room
from app.models.chat_message import ChatMessage
from app.models.chat_room import ChatRoom
from app.models.user import User
from app.schemas.chat_room import CreateChatRoomRequest
from app.websocket.manager import manager
from app.services.ai_service import AIService, AIServiceError
from app.services.ai_context_service import AIContextService
from app.services.chat_attachment_service import ChatAttachmentService

class ChatService:

    def __init__(self, db: Session):
        self.db = db
        self.ai = AIService()

    def _notify_chat_recipient(
        self,
        room: ChatRoom,
        sender: User,
        preview: str,
    ) -> None:
        if room.is_ai:
            return
        recipient_id = (
            room.pakar_id if sender.id == room.peternak_id else room.peternak_id
        )
        if recipient_id is None:
            return
        notification_crud.create(
            self.db,
            user_id=recipient_id,
            title=f"Pesan baru dari {sender.fullname}",
            message=preview[:180],
            notification_type=NotificationType.INFO,
            category=NotificationCategory.CHAT,
        )

    def list_rooms(
        self,
        current_user: User,
    ):

        if current_user.role == UserRole.PETERNAK:

            ai_room = chat_room.get_ai_room(
                self.db,
                current_user.id,
            )

            if ai_room is None:

                chat_room.create(
                    self.db,
                    peternak_id=current_user.id,
                    pakar_id=None,
                    title="AI Assistant",
                    is_ai=True,
                )

            rooms = chat_room.get_by_peternak(
                self.db,
                current_user.id,
            )
            return [self._serialize_room(room, current_user) for room in rooms]

        rooms = chat_room.get_by_pakar(
            self.db,
            current_user.id,
        )
        return [self._serialize_room(room, current_user) for room in rooms]

    def _serialize_room(self, room: ChatRoom, current_user: User) -> dict:
        last_message = chat_message.get_last_message(self.db, room.id)
        return {
            "id": room.id,
            "peternak_id": room.peternak_id,
            "pakar_id": room.pakar_id,
            "title": room.title,
            "is_ai": room.is_ai,
            "is_closed": room.is_closed,
            "last_message": last_message.message if last_message else room.last_message,
            "last_message_at": (
                last_message.created_at if last_message else room.last_message_at
            ),
            "created_at": room.created_at,
            "pakar_photo_url": room.pakar_photo_url,
            "peternak_photo_url": room.peternak_photo_url,
            "peternak_name": room.peternak_name,
            "pakar_name": room.pakar_name,
            "unread_count": chat_message.count_unread(
                self.db,
                room.id,
                current_user.id,
            ),
            "last_message_sender_id": (
                last_message.sender_id if last_message else None
            ),
            "last_message_is_read": (
                last_message.is_read if last_message else None
            ),
        }

    def create_pakar_room(
        self,
        peternak: User,
        pakar: User,
    ) -> ChatRoom:

        if peternak.id == pakar.id:
            raise ValueError("Tidak dapat membuat room dengan diri sendiri")

        if pakar.role != UserRole.PAKAR:
            raise ValueError("User bukan pakar")

        room = chat_room.get_pakar_room(
            self.db,
            peternak.id,
            pakar.id,
        )

        if room:
            # Sebelumnya `get_pakar_room` cuma nyari room yang masih
            # `is_closed=False`, jadi kalau room lama pernah ditutup,
            # code ini gak pernah ketemu dan jatuh ke `chat_room.create`
            # di bawah -> bikin room baru yang kosong (last_message
            # null) padahal histori chat lama masih ada di room
            # satunya. Sekarang `get_pakar_room` mengembalikan room
            # apapun statusnya, jadi tinggal reopen room yang sama.
            if room.is_closed:
                room = chat_room.reopen(self.db, room)
            return room

        return chat_room.create(
            self.db,
            peternak_id=peternak.id,
            pakar_id=pakar.id,
            title=pakar.fullname,
            is_ai=False,
        )

    def get_messages(
        self,
        room_id: UUID,
        current_user: User,
    ):

        room = chat_room.get(
            self.db,
            room_id,
        )

        if room is None:
            raise ValueError("Room tidak ditemukan")

        self._validate_room_access(
            room,
            current_user,
        )

        chat_message.mark_as_read(
            self.db,
            room.id,
            current_user.id,
        )

        return chat_message.get_messages(
            self.db,
            room.id,
        )
    
    async def send_ai_message(
        self,
        room: ChatRoom,
        current_user: User,
        message: str,
    ):
        # simpan pesan user

        user_message = chat_message.create(
            self.db,
            room_id=room.id,
            sender_id=current_user.id,
            message=message,
        )

        await manager.broadcast(
            str(room.id),
            {
                "type": "new_message",
                "message": user_message.message,
                "sender_id": str(user_message.sender_id),
                "room_id": str(room.id),
            },
        )

        return await self._generate_ai_reply(
            room=room,
            current_user=current_user,
            prompt=message,
        )

    async def _generate_ai_reply(
        self,
        room: ChatRoom,
        current_user: User,
        prompt: str,
        image_contents: bytes | None = None,
        image_mime_type: str | None = None,
    ) -> ChatMessage:
        await manager.broadcast(
            str(room.id),
            {"type": "typing_start", "room_id": str(room.id)},
        )

        try:
            ai_context = AIContextService(self.db).build_for_peternak(current_user)
            reply = await self.ai.chat(
                prompt,
                ai_context,
                image_contents=image_contents,
                image_mime_type=image_mime_type,
            )

            # Kirim jawaban final bertahap sebagai delta kata. Ini bukan
            # chain-of-thought model; hanya animasi streaming jawaban yang
            # aman untuk ditampilkan kepada pengguna.
            chunks = re.findall(r"\S+\s*", reply)
            chunk_delay = min(0.045, max(0.008, 12 / max(len(chunks), 1)))
            for chunk in chunks:
                await manager.broadcast(
                    str(room.id),
                    {
                        "type": "ai_chunk",
                        "room_id": str(room.id),
                        "delta": chunk,
                    },
                )
                await asyncio.sleep(chunk_delay)
        except AIServiceError as exc:
            await manager.broadcast(
                str(room.id),
                {
                    "type": "typing_error",
                    "room_id": str(room.id),
                    "message": str(exc),
                },
            )
            raise ValueError(str(exc)) from exc
        finally:
            await manager.broadcast(
                str(room.id),
                {"type": "typing_end", "room_id": str(room.id)},
            )

        ai_message = chat_message.create(
            self.db,
            room_id=room.id,
            sender_id=None,
            message=reply,
        )

        await manager.broadcast(
            str(room.id),
            {
                "type": "new_message",
                "message": ai_message.message,
                "sender_id": None,
                "room_id": str(room.id),
            },
        )

        chat_room.update_last_message(
            self.db,
            room,
            reply,
        )

        return ai_message

    async def send_attachment(
        self,
        room_id: UUID,
        current_user: User,
        file: UploadFile,
    ) -> ChatMessage:
        room = chat_room.get(self.db, room_id)
        if room is None:
            raise ValueError("Room tidak ditemukan")
        self._validate_room_access(room, current_user)
        if room.is_closed:
            raise ValueError("Room sudah ditutup")
        if room.is_ai and not (file.content_type or "").startswith("image/"):
            raise ValueError("AI Assistant saat ini hanya menerima lampiran foto.")

        attachment = await ChatAttachmentService().store(str(room.id), file)
        if room.is_ai and attachment.message_type.value != "image":
            raise ValueError("AI Assistant saat ini hanya menerima lampiran foto.")

        message = chat_message.create(
            self.db,
            room_id=room.id,
            sender_id=current_user.id,
            message=attachment.display_name,
            message_type=attachment.message_type,
            attachment_url=attachment.url,
        )
        self._notify_chat_recipient(
            room,
            current_user,
            f"Mengirim {attachment.message_type.value}: {attachment.display_name}",
        )
        chat_room.update_last_message(
            self.db,
            room,
            f"Mengirim {attachment.message_type.value}",
        )
        await manager.broadcast(
            str(room.id),
            {
                "type": "new_message",
                "message": message.message,
                "sender_id": str(message.sender_id),
                "room_id": str(room.id),
            },
        )

        if room.is_ai:
            return await self._generate_ai_reply(
                room=room,
                current_user=current_user,
                prompt=(
                    "Analisis foto ini dalam konteks data SilaseZ milik saya. "
                    "Jelaskan temuan yang terlihat, keterbatasan analisis foto, "
                    "dan langkah praktis yang aman."
                ),
                image_contents=attachment.contents,
                image_mime_type=attachment.content_type,
            )
        return message
    

    async def send_message(
        self,
        room_id: UUID,
        current_user: User,
        message: str,
    ):
        room = chat_room.get(
            self.db,
            room_id,
        )

        if room is None:
            raise ValueError("Room tidak ditemukan")

        self._validate_room_access(
            room,
            current_user,
        )

        if room.is_closed:
            raise ValueError("Room sudah ditutup")

        if room.is_ai:
            return await self.send_ai_message(
                room,
                current_user,
                message,
            )
        
        msg = chat_message.create(
            self.db,
            room_id=room.id,
            sender_id=current_user.id,
            message=message,
        )

        self._notify_chat_recipient(room, current_user, message)

        # from app.websocket.manager import manager

        

        chat_room.update_last_message(
            self.db,
            room,
            message,
        )

        await manager.broadcast(
            str(room.id),
            {
                "type": "new_message",
                "message": msg.message,
                "sender_id": str(msg.sender_id),
                "room_id": str(room.id),
            },
        )

        return msg
    
    def create_room(
        self,
        current_user: User,
        data: CreateChatRoomRequest,
    ) -> ChatRoom:

        if current_user.role != UserRole.PETERNAK:
            raise PermissionError(
                "Hanya peternak yang dapat membuat room."
            )

        pakar = (
            self.db.query(User)
            .filter(
                User.id == data.pakar_id,
                User.role == UserRole.PAKAR,
                User.is_active.is_(True),
            )
            .first()
        )

        if pakar is None:
            raise ValueError("Pakar tidak ditemukan")

        return self.create_pakar_room(
            current_user,
            pakar,
        )
    
    # def get_rooms(
    #     self,
    #     current_user: User,
    # ):

    #     if current_user.role == UserRole.PETERNAK:
    #         return chat_room.get_by_peternak(
    #             self.db,
    #             current_user.id,
    #         )

    #     if current_user.role == UserRole.PAKAR:
    #         return chat_room.get_by_pakar(
    #             self.db,
    #             current_user.id,
    #         )

    #     return []
    def close_room(
        self,
        room_id: UUID,
        current_user: User,
    ):

        room = chat_room.get(
            self.db,
            room_id,
        )

        if room is None:
            raise ValueError("Room tidak ditemukan")

        self._validate_room_access(
            room,
            current_user,
        )

        chat_room.close(
            self.db,
            room,
        )
  


    def _validate_room_access(
        self,
        room: ChatRoom,
        user: User,
    ):

        if user.role == UserRole.ADMIN:
            return

        if user.role == UserRole.PETERNAK:
            if room.peternak_id != user.id:
                raise PermissionError("Tidak memiliki akses ke room ini")
            return

        if user.role == UserRole.PAKAR:
            if room.is_ai:
                raise PermissionError("Room AI hanya dapat diakses peternak")

            if room.pakar_id != user.id:
                raise PermissionError("Tidak memiliki akses ke room ini")
            return

        raise PermissionError("Role tidak diizinkan")
