from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.core.enums import FermentationStatus


class StartFermentationRequest(BaseModel):
    # Default hari ini kalau tidak diisi (lihat FermentationService.start).
    start_date: date | None = None
    planned_duration_days: Literal[21] = 21
    catatan: str | None = None


class CompleteFermentationRequest(BaseModel):
    # Cuma boleh COMPLETED atau CANCELLED — divalidasi di
    # FermentationService.finish (RUNNING gak masuk akal buat "menutup"
    # siklus, itu status awal).
    status: FermentationStatus
    catatan: str | None = None


class FermentationCycleResponse(BaseModel):
    id: UUID
    silo_id: UUID
    silo_nama: str
    peternakan_id: UUID | None

    start_date: date
    end_date: date
    actual_end_date: date | None
    planned_duration_days: int

    # Dihitung dari property model (lihat app/models/fermentation_cycle.py),
    # bukan disimpan, supaya selalu akurat tiap di-fetch.
    current_day: int
    is_overdue: bool
    start_day_name: str
    end_day_name: str

    status: FermentationStatus
    catatan: str | None

    created_at: datetime

    model_config = {
        "from_attributes": True
    }
