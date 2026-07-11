from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.enums import FermentationStatus, SensorStatus, SiloStatus
from app.schemas.fermentation import FermentationCycleResponse
from app.schemas.peternakan import LokasiResponse


class PakarOwnerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    fullname: str
    phone: str | None


class LatestSensorReadingResponse(BaseModel):
    id: UUID
    sensor_id: UUID
    device_id: str
    sensor_nama: str
    temperature: float
    humidity: float
    ph: float
    methane: float
    ammonia: float
    co2: float
    recorded_at: datetime


class PakarSiloConditionResponse(BaseModel):
    id: UUID
    nama: str
    kapasitas: int
    status: SiloStatus
    sensor_statuses: list[SensorStatus]
    kondisi: str
    fermentasi_aktif: FermentationCycleResponse | None
    pembacaan_terbaru: LatestSensorReadingResponse | None


class PakarPeternakanSummaryResponse(BaseModel):
    id: UUID
    nama: str
    alamat: str | None
    jenis_ternak: str
    jumlah_ternak: int
    jenis_pakan: str
    owner: PakarOwnerResponse
    lokasi: LokasiResponse
    jumlah_silo: int
    kondisi: str
    pembacaan_terakhir_at: datetime | None


class PakarPeternakanDetailResponse(PakarPeternakanSummaryResponse):
    silos: list[PakarSiloConditionResponse]


class SensorHistoryResponse(LatestSensorReadingResponse):
    silo_id: UUID
    silo_nama: str


class PakarPeternakanHistoryResponse(BaseModel):
    peternakan_id: UUID
    sensor_logs: list[SensorHistoryResponse]
    fermentation_cycles: list[FermentationCycleResponse]

