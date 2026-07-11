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
    humidity: float
    ph: float
    methane: float
    ammonia: float
    co2: float
    recorded_at: datetime
