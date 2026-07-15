from uuid import UUID

from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Index, Integer, String

from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.mixins import UUIDMixin
from app.models.mixins import TimestampMixin


class SensorLog(
    Base,
    UUIDMixin,
    TimestampMixin,
):
    __tablename__ = "sensor_logs"

    sensor_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sensors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    fermentation_cycle_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("fermentation_cycles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    temperature: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    humidity: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    methane: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    ammonia: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    co2: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    ph: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    fermentation_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    phase: Mapped[str] = mapped_column(
        String(30), nullable=False, default="monitoring"
    )
    classification: Mapped[str | None] = mapped_column(String(80), nullable=True)

    @property
    def water_content(self) -> float:
        return self.humidity

    @property
    def delta_gas(self) -> float:
        return self.methane

    sensor = relationship(
        "Sensor",
        back_populates="logs",
    )

    fermentation_cycle = relationship("FermentationCycle")


Index("idx_sensor_created", SensorLog.sensor_id, SensorLog.created_at)
