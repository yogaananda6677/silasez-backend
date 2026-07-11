from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.dependencies import get_db
from app.models.user import User
from app.schemas.pakar import (
    PakarPeternakanDetailResponse,
    PakarPeternakanHistoryResponse,
    PakarPeternakanSummaryResponse,
)
from app.services.pakar_service import PakarService


router = APIRouter(prefix="/pakar", tags=["Pakar"])


@router.get("/peternakan", response_model=list[PakarPeternakanSummaryResponse])
def list_peternakan_for_pakar(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return PakarService(db).list_peternakan(current_user)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/peternakan/{peternakan_id}", response_model=PakarPeternakanDetailResponse)
def get_peternakan_for_pakar(
    peternakan_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return PakarService(db).get_peternakan(current_user, peternakan_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get(
    "/peternakan/{peternakan_id}/riwayat",
    response_model=PakarPeternakanHistoryResponse,
)
def get_peternakan_history_for_pakar(
    peternakan_id: UUID,
    sensor_limit: int = Query(default=100, ge=1, le=500),
    fermentation_limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        service = PakarService(db)
        service.require_pakar(current_user)
        return service.get_history(
            current_user,
            peternakan_id,
            sensor_limit,
            fermentation_limit,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
