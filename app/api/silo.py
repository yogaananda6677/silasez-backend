from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.dependencies import get_db
from app.models.user import User
from app.schemas.silo import SiloCreateRequest, SiloResponse, SiloUpdateRequest
from app.schemas.sensor import LatestSensorReadingResponse, SensorChartResponse
from app.services.silo_service import SiloService

router = APIRouter(tags=["Silo"])


@router.post("/peternakan/{peternakan_id}/silo", response_model=SiloResponse, status_code=201)
def create_silo(
    peternakan_id: UUID,
    data: SiloCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = SiloService(db)

    try:
        return service.create(current_user, peternakan_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/peternakan/{peternakan_id}/silo", response_model=list[SiloResponse])
def list_silo(
    peternakan_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = SiloService(db)

    try:
        return service.list_for_peternakan(current_user, peternakan_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/silo/{silo_id}", response_model=SiloResponse)
def get_silo(
    silo_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = SiloService(db)

    try:
        return service.get_readable(current_user, silo_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get(
    "/silo/{silo_id}/sensor/terbaru",
    response_model=LatestSensorReadingResponse | None,
)
def get_latest_sensor_reading(
    silo_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = SiloService(db)
    try:
        return service.get_latest_sensor_reading(current_user, silo_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.get(
    "/silo/{silo_id}/sensor/grafik",
    response_model=SensorChartResponse,
)
def get_sensor_chart(
    silo_id: UUID,
    day_from: int = Query(default=1, ge=1, le=21),
    day_to: int = Query(default=5, ge=1, le=21),
    selected_day: int | None = Query(default=None, ge=1, le=21),
    fermentation_cycle_id: UUID | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return SiloService(db).get_sensor_chart(
            current_user,
            silo_id,
            day_from,
            day_to,
            selected_day,
            fermentation_cycle_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.patch("/silo/{silo_id}", response_model=SiloResponse)
def update_silo(
    silo_id: UUID,
    data: SiloUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = SiloService(db)

    try:
        return service.update(current_user, silo_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/silo/{silo_id}", status_code=204)
def delete_silo(
    silo_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = SiloService(db)

    try:
        service.delete(current_user, silo_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
