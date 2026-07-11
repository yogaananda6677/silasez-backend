from uuid import UUID

from sqlalchemy import nulls_last
from sqlalchemy.orm import Session

from app.models.chat_room import ChatRoom
from datetime import datetime


class CRUDChatRoom:

    def create(
        self,
        db: Session,
        *,
        peternak_id: UUID,
        pakar_id: UUID | None,
        title: str | None,
        is_ai: bool,
    ) -> ChatRoom:

        room = ChatRoom(
            peternak_id=peternak_id,
            pakar_id=pakar_id,
            title=title,
            is_ai=is_ai,
        )

        db.add(room)
        db.commit()
        db.refresh(room)

        return room

    def get(
        self,
        db: Session,
        room_id: UUID,
    ) -> ChatRoom | None:

        return (
            db.query(ChatRoom)
            .filter(ChatRoom.id == room_id)
            .first()
        )
    
    def get_by_id(
        self,
        db: Session,
        room_id: UUID,
    ) -> ChatRoom | None:

        return (
            db.query(ChatRoom)
            .filter(ChatRoom.id == room_id)
            .first()
        )
    
    def get_by_pakar(
        self,
        db: Session,
        pakar_id: UUID,
    ):

        return (
            db.query(ChatRoom)
            .filter(
                ChatRoom.pakar_id == pakar_id,
            )
            .order_by(
                nulls_last(ChatRoom.last_message_at.desc())
            )
            .all()
        )

    def get_by_peternak(
        self,
        db: Session,
        peternak_id: UUID,
    ) -> list[ChatRoom]:

        return (
            db.query(ChatRoom)
            .filter(ChatRoom.peternak_id == peternak_id)
            .order_by(nulls_last(ChatRoom.last_message_at.desc()))
            .all()
        )

    def get_ai_room(
        self,
        db: Session,
        peternak_id: UUID,
    ) -> ChatRoom | None:

        return (
            db.query(ChatRoom)
            .filter(
                ChatRoom.peternak_id == peternak_id,
                ChatRoom.is_ai.is_(True),
                ChatRoom.is_closed.is_(False),
            )
            .first()
        )

    def get_pakar_room(
        self,
        db: Session,
        peternak_id: UUID,
        pakar_id: UUID,
    ) -> ChatRoom | None:
        """Cari room peternak-pakar ini TANPA filter `is_closed`, supaya
        kalau room lama sudah pernah ditutup, service bisa reopen room
        yang sama (lihat `ChatService.create_pakar_room`) alih-alih
        bikin room baru yang kosong & memutus histori chat lama."""

        return (
            db.query(ChatRoom)
            .filter(
                ChatRoom.peternak_id == peternak_id,
                ChatRoom.pakar_id == pakar_id,
            )
            .first()
        )

    def update_last_message(
        self,
        db: Session,
        room: ChatRoom,
        message: str,
    ) -> ChatRoom:

        room.last_message = message

        room.last_message_at = datetime.utcnow()

        db.commit()

        db.refresh(room)

        return room
    
    def reopen(
        self,
        db: Session,
        room: ChatRoom,
    ):

        room.is_closed = False

        db.commit()

        db.refresh(room)

        return room

    def close(
        self,
        db: Session,
        room: ChatRoom,
    ):

        room.is_closed = True

        db.commit()

    def has_consulted(
        self,
        db: Session,
        *,
        pakar_id: UUID,
        peternak_id: UUID,
    ) -> bool:
        """Dipakai buat otorisasi read-only ke data monitoring ternak
        (Silo & FermentationCycle, lihat `SiloService`/`FermentationService`):
        pakar boleh baca data peternak X kalau pernah/sedang punya
        ChatRoom konsultasi (bukan AI) dengan peternak itu. Sengaja tidak
        difilter `is_closed`, karena chat yang sudah ditutup bukan berarti
        hubungan konsultasi/monitoring-nya ikut dicabut."""

        return (
            db.query(ChatRoom)
            .filter(
                ChatRoom.pakar_id == pakar_id,
                ChatRoom.peternak_id == peternak_id,
                ChatRoom.is_ai.is_(False),
            )
            .first()
            is not None
        )


chat_room = CRUDChatRoom()