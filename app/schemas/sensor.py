from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.core.enums import SensorStatus


class SensorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    device_id: str
    nama: str
    tipe: str
    status: SensorStatus
    silo_id: UUID | None
    created_at: datetime


class LatestSensorReadingResponse(BaseModel):
    id: UUID
    sensor_id: UUID
    device_id: str
    sensor_nama: str
    silo_id: UUID
    temperature: float
    water_content: float
    ph: float
    delta_gas: float
    fermentation_day: int | None
    phase: str
    classification: str | None
    recorded_at: datetime
