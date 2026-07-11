from pydantic import BaseModel, EmailStr, Field
from uuid import UUID

from app.core.enums import SensorStatus, SiloStatus


class CreatePakarRequest(BaseModel):
    fullname: str = Field(..., min_length=3)
    email: EmailStr
    password: str = Field(..., min_length=8)
    phone: str = Field(..., min_length=10)


class ApproveDeviceRequest(BaseModel):
    silo_id: UUID
    nama: str = Field(..., min_length=3)
    tipe: str = Field(default="esp32")


class AdminSiloResponse(BaseModel):
    id: UUID
    nama: str
    kapasitas: int
    status: SiloStatus
    sensor_count: int
    active_cycle_count: int


class AdminFarmResponse(BaseModel):
    id: UUID
    nama: str
    alamat: str | None
    jenis_ternak: str
    jumlah_ternak: int
    jenis_pakan: str
    owner_id: UUID
    owner_name: str
    owner_email: str
    silos: list[AdminSiloResponse]


class AdminOverviewResponse(BaseModel):
    total_users: int
    total_peternakan: int
    total_silos: int
    active_cycles: int
    pending_devices: int
    peternakan: list[AdminFarmResponse]
