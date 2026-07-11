from uuid import UUID

from pydantic import BaseModel, Field


class LokasiResponse(BaseModel):
    id: UUID
    latitude: float
    longitude: float
    provinsi: str
    kabupaten: str
    kecamatan: str
    desa: str
    alamat_lengkap: str | None

    model_config = {
        "from_attributes": True
    }


class PeternakanCreateRequest(BaseModel):
    nama: str
    alamat: str | None = None

    jenis_ternak: str
    jumlah_ternak: int = Field(ge=0)
    jenis_pakan: str

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

class PeternakanUpdateRequest(BaseModel):
    nama: str | None = None
    alamat: str | None = None

    jenis_ternak: str | None = None
    jumlah_ternak: int | None = Field(default=None, ge=0)
    jenis_pakan: str | None = None

    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

class PeternakanResponse(BaseModel):
    id: UUID

    nama: str
    alamat: str | None

    jenis_ternak: str
    jumlah_ternak: int
    jenis_pakan: str

    lokasi: LokasiResponse

    model_config = {
        "from_attributes": True
    }