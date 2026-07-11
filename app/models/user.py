from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import UserRole
from app.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.chat_room import ChatRoom
    from app.models.notification import Notification
    from app.models.peternakan import Peternakan


class User(
    Base,
    UUIDMixin,
    TimestampMixin,
    SoftDeleteMixin,
):
    __tablename__ = "users"

    fullname: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False,
        index=True,
    )

    password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            name="user_role",
        ),
        default=UserRole.PETERNAK,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    photo_url: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # ==========================
    # Relationship
    # ==========================

    peternakan: Mapped[list["Peternakan"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
    )

    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    peternak_rooms: Mapped[list["ChatRoom"]] = relationship(
        foreign_keys="ChatRoom.peternak_id",
        back_populates="peternak",
    )

    pakar_rooms: Mapped[list["ChatRoom"]] = relationship(
        foreign_keys="ChatRoom.pakar_id",
        back_populates="pakar",
    )

    def __repr__(self) -> str:
        return (
            f"<User("
            f"id={self.id}, "
            f"fullname='{self.fullname}', "
            f"email='{self.email}', "
            f"role='{self.role.value}'"
            f")>"
        )