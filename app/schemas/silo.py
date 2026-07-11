from uuid import UUID

from pydantic import BaseModel, Field

from app.core.enums import SiloStatus


class SiloCreateRequest(BaseModel):
    nama: str
    kapasitas: int = Field(gt=0)


class SiloUpdateRequest(BaseModel):
    nama: str | None = None
    kapasitas: int | None = Field(default=None, gt=0)
    status: SiloStatus | None = None


class SiloResponse(BaseModel):
    id: UUID
    peternakan_id: UUID

    nama: str
    kapasitas: int
    status: SiloStatus

    model_config = {
        "from_attributes": True
    }
