from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.dependencies import get_db
from app.core.enums import UserRole

from app.models.user import User

from app.schemas.admin import (
    AdminOverviewResponse,
    ApproveDeviceRequest,
    CreatePakarRequest,
)
from app.schemas.sensor import SensorResponse
from app.schemas.user import UserResponse

from app.services.admin_service import AdminService

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)

def _require_admin(current_user: User):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Hanya admin yang dapat mengakses endpoint ini",
        )


@router.post(
    "/pakar",
    response_model=UserResponse,
    status_code=201,
)
def create_pakar(
    data: CreatePakarRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    _require_admin(current_user)

    service = AdminService(db)

    try:
        return service.create_pakar(data)

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.get("/overview", response_model=AdminOverviewResponse)
def get_admin_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(current_user)
    return AdminService(db).get_overview()


@router.get(
    "/devices/pending",
    response_model=list[SensorResponse],
)
def list_pending_devices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Daftar device ESP yang sudah connect & kirim data lewat MQTT
    tapi belum di-approve/assign ke silo manapun.
    """

    _require_admin(current_user)

    service = AdminService(db)

    return service.list_pending_devices()


@router.post(
    "/devices/{sensor_id}/approve",
    response_model=SensorResponse,
)
def approve_device(
    sensor_id: UUID,
    data: ApproveDeviceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Approve device pending: assign ke silo tertentu, kasih nama,
    status berubah jadi ACTIVE sehingga data sensornya mulai disimpan.
    """

    _require_admin(current_user)

    service = AdminService(db)

    try:
        return service.approve_device(sensor_id, data)

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )
