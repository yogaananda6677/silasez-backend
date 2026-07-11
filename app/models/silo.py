from uuid import UUID

from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String

from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.enums import SiloStatus
from app.models.mixins import UUIDMixin
from app.models.mixins import TimestampMixin
from app.models.mixins import SoftDeleteMixin


class Silo(
    Base,
    UUIDMixin,
    TimestampMixin,
    SoftDeleteMixin,
):
    __tablename__ = "silos"

    peternakan_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("peternakan.id", ondelete="CASCADE"),
        nullable=False,
    )

    nama: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    kapasitas: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    status: Mapped[SiloStatus] = mapped_column(
        Enum(SiloStatus, name="silo_status"),
        default=SiloStatus.ACTIVE,
        nullable=False,
    )

    peternakan = relationship(
        "Peternakan",
        back_populates="silos",
    )

    sensors = relationship(
        "Sensor",
        back_populates="silo",
        cascade="all, delete-orphan",
    )

    fermentation_cycles = relationship(
        "FermentationCycle",
        back_populates="silo",
        cascade="all, delete-orphan",
    )