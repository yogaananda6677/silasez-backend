from sqlalchemy import Float
from sqlalchemy import String

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.core.database import Base

from app.models.mixins import TimestampMixin
from app.models.mixins import UUIDMixin


class Lokasi(
    Base,
    UUIDMixin,
    TimestampMixin,
):
    __tablename__ = "lokasi"

    latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    provinsi: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    kabupaten: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    kecamatan: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    desa: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    alamat_lengkap: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
    )

    peternakan = relationship(
        "Peternakan",
        back_populates="lokasi",
        uselist=False,
    )