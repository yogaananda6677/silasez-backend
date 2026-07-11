from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    PETERNAK = "peternak"
    PAKAR = "pakar"


class FarmStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class SiloStatus(str, Enum):
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"


class FermentationStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SensorStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    OFFLINE = "offline"
    ERROR = "error"


class NotificationType(str, Enum):
    INFO = "info"
    WARNING = "warning"
    DANGER = "danger"


class ChatSender(str, Enum):
    USER = "user"
    PAKAR = "pakar"
    SYSTEM = "system"

class MessageType(str, Enum):

    TEXT="text"

    IMAGE="image"

    VIDEO="video"

    FILE="file"

    LOCATION="location"

    SYSTEM="system"
