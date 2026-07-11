from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.dependencies import get_db
from app.models.user import User
from app.schemas.peternakan import (
    PeternakanCreateRequest,
    PeternakanResponse,
    PeternakanUpdateRequest,
)
from app.schemas.pakar import PakarPeternakanHistoryResponse
from app.services.pakar_service import PakarService
from app.services.peternakan_service import PeternakanService

router = APIRouter(
    prefix="/peternakan",
    tags=["Peternakan"],
)


@router.post("", response_model=PeternakanResponse, status_code=201)
def create_peternakan(
    data: PeternakanCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = PeternakanService(db)

    try:
        return service.create(current_user, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[PeternakanResponse])
def list_peternakan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = PeternakanService(db)
    return service.list_mine(current_user)


@router.get("/{peternakan_id}", response_model=PeternakanResponse)
def get_peternakan(
    peternakan_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = PeternakanService(db)

    try:
        return service.get_owned(current_user, peternakan_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get(
    "/{peternakan_id}/riwayat",
    response_model=PakarPeternakanHistoryResponse,
)
def get_peternakan_history(
    peternakan_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Riwayat untuk pemilik atau pakar yang memiliki relasi konsultasi."""
    try:
        return PakarService(db).get_history(
            current_user,
            peternakan_id,
            sensor_limit=500,
            fermentation_limit=200,
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.patch("/{peternakan_id}", response_model=PeternakanResponse)
def update_peternakan(
    peternakan_id: UUID,
    data: PeternakanUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = PeternakanService(db)

    try:
        return service.update(current_user, peternakan_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{peternakan_id}", status_code=204)
def delete_peternakan(
    peternakan_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = PeternakanService(db)

    try:
        service.delete(current_user, peternakan_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
