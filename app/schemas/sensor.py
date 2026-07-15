from uuid import UUID
from datetime import date, datetime
from typing import Literal

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


class SensorChartTimelineItem(BaseModel):
    day: int
    date: date
    has_data: bool
    reading_count: int
    selected: bool


class SensorChartPoint(BaseModel):
    day: int
    date: date
    reading_count: int
    temperature_avg: float
    temperature_min: float
    temperature_max: float
    water_content_avg: float
    water_content_min: float
    water_content_max: float
    ph_avg: float
    ph_min: float
    ph_max: float
    delta_gas_avg: float
    delta_gas_min: float
    delta_gas_max: float
    classification: str | None


class SensorChartReading(BaseModel):
    id: UUID
    sensor_id: UUID
    device_id: str
    sensor_nama: str
    temperature: float
    water_content: float
    ph: float
    delta_gas: float
    classification: str | None
    recorded_at: datetime


class SensorChartAnalysis(BaseModel):
    status: Literal["baik", "perlu_perhatian", "belum_ada_data"]
    ringkasan: str
    saran: list[str]
    temperature_trend: Literal["naik", "turun", "stabil", "belum_cukup_data"]
    water_content_trend: Literal["naik", "turun", "stabil", "belum_cukup_data"]
    ph_trend: Literal["naik", "turun", "stabil", "belum_cukup_data"]
    delta_gas_trend: Literal["naik", "turun", "stabil", "belum_cukup_data"]


class SensorChartResponse(BaseModel):
    silo_id: UUID
    fermentation_cycle_id: UUID
    start_date: date
    end_date: date
    planned_duration_days: int
    current_day: int
    day_from: int
    day_to: int
    selected_day: int | None
    timeline: list[SensorChartTimelineItem]
    chart: list[SensorChartPoint]
    selected_day_readings: list[SensorChartReading]
    analysis: SensorChartAnalysis
