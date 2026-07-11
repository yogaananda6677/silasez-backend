from uuid import UUID

from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.crud.chat_message import chat_message
from app.crud.chat_room import chat_room
from app.models.chat_message import ChatMessage
from app.models.chat_room import ChatRoom
from app.models.user import User
from app.schemas.chat_message import SendMessageRequest
from app.schemas.chat_room import CreateChatRoomRequest
from app.models.user import User
from app.websocket.manager import manager
from app.services.ai_service import AIService

class ChatService:

    def __init__(self, db: Session):
        self.db = db
        self.ai = AIService()

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

            return chat_room.get_by_peternak(
                self.db,
                current_user.id,
            )

        return chat_room.get_by_pakar(
            self.db,
            current_user.id,
        )

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

        reply = await self.ai.chat(message)

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
    

    async def send_message(
        self,
        room_id: UUID,
        current_user: User,
        message: str,
    ):
        print("========== MASUK AI ==========")
        print(room_id)
        print(message)
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


