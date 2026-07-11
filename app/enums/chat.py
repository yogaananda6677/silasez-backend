from enum import Enum


class ChatRoomType(str, Enum):
    AI = "AI"
    PAKAR = "PAKAR"


class ChatRoomStatus(str, Enum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"


class MessageType(str, Enum):
    TEXT = "TEXT"