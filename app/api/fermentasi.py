from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.dependencies import get_db
from app.models.user import User
from app.schemas.fermentation import (
    CompleteFermentationRequest,
    FermentationCycleResponse,
    StartFermentationRequest,
)
from app.services.fermentation_service import FermentationService

router = APIRouter(tags=["Fermentasi"])


@router.post(
    "/silo/{silo_id}/fermentasi/mulai",
    response_model=FermentationCycleResponse,
    status_code=201,
)
def start_fermentation(
    silo_id: UUID,
    data: StartFermentationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = FermentationService(db)

    try:
        return service.start(current_user, silo_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get(
    "/silo/{silo_id}/fermentasi/aktif",
    response_model=Optional[FermentationCycleResponse],
)
def get_active_fermentation(
    silo_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = FermentationService(db)

    try:
        return service.get_active(current_user, silo_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get(
    "/silo/{silo_id}/fermentasi",
    response_model=list[FermentationCycleResponse],
)
def list_fermentation_history(
    silo_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = FermentationService(db)

    try:
        return service.list_history(current_user, silo_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post(
    "/fermentasi/{cycle_id}/selesai",
    response_model=FermentationCycleResponse,
)
def finish_fermentation(
    cycle_id: UUID,
    data: CompleteFermentationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = FermentationService(db)

    try:
        return service.finish(current_user, cycle_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
