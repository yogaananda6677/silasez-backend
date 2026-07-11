from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy import String

from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.core.database import Base

from app.models.mixins import TimestampMixin
from app.models.mixins import UUIDMixin
from app.models.mixins import SoftDeleteMixin


class Peternakan(
    Base,
    UUIDMixin,
    TimestampMixin,
    SoftDeleteMixin,
):
    __tablename__ = "peternakan"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    lokasi_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("lokasi.id"),
        nullable=False,
    )

    nama: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    alamat: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
    )

    jenis_ternak: Mapped[str] = mapped_column(
    String(100),
    nullable=False,
)

    jumlah_ternak: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )

    jenis_pakan: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    owner = relationship(
        "User",
        back_populates="peternakan",
    )

    lokasi = relationship(
        "Lokasi",
        back_populates="peternakan",
        uselist=False,
    )

    silos = relationship(
        "Silo",
        back_populates="peternakan",
        cascade="all, delete-orphan",
    )