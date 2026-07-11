from uuid import UUID

from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Index

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

    sensor = relationship(
        "Sensor",
        back_populates="logs",
    )


Index("idx_sensor_created", SensorLog.sensor_id, SensorLog.created_at)