from uuid import UUID

from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import String

from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.enums import SensorStatus
from app.models.mixins import UUIDMixin
from app.models.mixins import TimestampMixin


class Sensor(
    Base,
    UUIDMixin,
    TimestampMixin,
):
    __tablename__ = "sensors"

    silo_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("silos.id", ondelete="CASCADE"),
        nullable=True,
    )

    device_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    nama: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    tipe: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    status: Mapped[SensorStatus] = mapped_column(
            Enum(SensorStatus, name="sensor_status"),
            default=SensorStatus.ACTIVE,
            nullable=False,
        )

    silo = relationship(
        "Silo",
        back_populates="sensors",
    )

    logs = relationship(
        "SensorLog",
        back_populates="sensor",
        cascade="all, delete-orphan",
    )