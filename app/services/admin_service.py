from uuid import UUID

from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.crud.user import (
    create_user,
    get_by_email,
)
from app.crud import sensor as sensor_crud
from app.schemas.admin import ApproveDeviceRequest, CreatePakarRequest


class AdminService:

    def __init__(self, db: Session):
        self.db = db

    def create_pakar(
        self,
        data: CreatePakarRequest,
    ):

        existing = get_by_email(
            self.db,
            data.email,
        )

        if existing:
            raise ValueError("Email sudah digunakan")

        return create_user(
            self.db,
            fullname=data.fullname,
            email=data.email,
            password=data.password,   # <-- TANPA hash
            phone=data.phone,
            role=UserRole.PAKAR,
        )

    def list_pending_devices(self):
        return sensor_crud.list_pending(self.db)

    def approve_device(
        self,
        sensor_id: UUID,
        data: ApproveDeviceRequest,
    ):
        sensor = sensor_crud.get_by_id(self.db, sensor_id)

        if sensor is None:
            raise ValueError("Device tidak ditemukan")

        return sensor_crud.approve_device(
            self.db,
            sensor=sensor,
            silo_id=data.silo_id,
            nama=data.nama,
            tipe=data.tipe,
        )