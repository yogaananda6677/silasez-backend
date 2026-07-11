from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.dependencies import get_db
from app.models.user import User

from app.schemas.chat_room import (
    ChatRoomResponse,
    CreateChatRoomRequest,
)

from app.schemas.chat_message import (
    ChatMessageResponse,
    SendMessageRequest,
)

from app.services.chat_service import ChatService


router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.get(
    "/rooms",
    response_model=list[ChatRoomResponse],
)
def list_rooms(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ChatService(db)

    try:
        return service.list_rooms(current_user)

    except PermissionError as e:
        raise HTTPException(
            status_code=403,
            detail=str(e),
        )


@router.post(
    "/rooms",
    response_model=ChatRoomResponse,
    status_code=201,
)
def create_room(
    data: CreateChatRoomRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ChatService(db)

    try:
        return service.create_room(
            current_user,
            data,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    except PermissionError as e:
        raise HTTPException(
            status_code=403,
            detail=str(e),
        )


@router.get(
    "/{room_id}/messages",
    response_model=list[ChatMessageResponse],
)
def get_messages(
    room_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ChatService(db)

    try:
        return service.get_messages(
            room_id,
            current_user,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )

    except PermissionError as e:
        raise HTTPException(
            status_code=403,
            detail=str(e),
        )


@router.post(
    "/{room_id}/messages",
    response_model=ChatMessageResponse,
    status_code=201,
)
async def send_message(
    room_id: UUID,
    data: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ChatService(db)

    try:
        return await service.send_message(
            room_id,
            current_user,
            data.message,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    except PermissionError as e:
        raise HTTPException(
            status_code=403,
            detail=str(e),
        )


@router.patch("/{room_id}/close")
def close_room(
    room_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ChatService(db)

    try:
        service.close_room(
            room_id,
            current_user,
        )

        return {
            "message": "Room berhasil ditutup",
        }

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )

    except PermissionError as e:
        raise HTTPException(
            status_code=403,
            detail=str(e),
        )