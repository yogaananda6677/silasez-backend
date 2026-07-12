from uuid import UUID

from sqlalchemy.orm import Session, selectinload, joinedload

from app.core.enums import FermentationStatus, SensorStatus, UserRole
from app.crud.user import (
    create_user,
    get_by_email,
)
from app.crud import sensor as sensor_crud
from app.crud import notification as notification_crud
from app.core.enums import NotificationCategory, NotificationType
from app.schemas.admin import ApproveDeviceRequest, CreatePakarRequest
from app.models.fermentation_cycle import FermentationCycle
from app.models.peternakan import Peternakan
from app.models.sensor import Sensor
from app.models.silo import Silo
from app.models.user import User


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
            password=data.password,
            phone=data.phone,
            role=UserRole.PAKAR,
        )

    def list_pending_devices(self):
        return sensor_crud.list_pending(self.db)

    def get_overview(self) -> dict:
        farms = (
            self.db.query(Peternakan)
            .options(
                joinedload(Peternakan.owner),
                selectinload(Peternakan.silos).selectinload(Silo.sensors),
                selectinload(Peternakan.silos).selectinload(Silo.fermentation_cycles),
            )
            .filter(Peternakan.is_deleted.is_(False))
            .order_by(Peternakan.created_at.desc())
            .all()
        )

        farm_items = []
        total_silos = 0
        active_cycles = 0
        for farm in farms:
            silos = []
            for silo in farm.silos:
                if silo.is_deleted:
                    continue
                active_count = sum(
                    cycle.status == FermentationStatus.RUNNING
                    for cycle in silo.fermentation_cycles
                )
                active_cycles += active_count
                total_silos += 1
                silos.append({
                    "id": silo.id,
                    "nama": silo.nama,
                    "kapasitas": silo.kapasitas,
                    "status": silo.status,
                    "sensor_count": len(silo.sensors),
                    "active_cycle_count": active_count,
                })
            farm_items.append({
                "id": farm.id,
                "nama": farm.nama,
                "alamat": farm.alamat,
                "jenis_ternak": farm.jenis_ternak,
                "jumlah_ternak": farm.jumlah_ternak,
                "jenis_pakan": farm.jenis_pakan,
                "owner_id": farm.owner.id,
                "owner_name": farm.owner.fullname,
                "owner_email": farm.owner.email,
                "silos": silos,
            })

        return {
            "total_users": self.db.query(User).filter(User.is_deleted.is_(False)).count(),
            "total_peternakan": len(farms),
            "total_silos": total_silos,
            "active_cycles": active_cycles,
            "pending_devices": self.db.query(Sensor)
                .filter(Sensor.status == SensorStatus.PENDING).count(),
            "peternakan": farm_items,
        }

    def approve_device(
        self,
        sensor_id: UUID,
        data: ApproveDeviceRequest,
    ):
        sensor = sensor_crud.get_by_id(self.db, sensor_id)

        if sensor is None:
            raise ValueError("Device tidak ditemukan")

        silo = self.db.query(Silo).filter(
            Silo.id == data.silo_id,
            Silo.is_deleted.is_(False),
        ).first()
        if silo is None:
            raise ValueError("Silo tujuan tidak ditemukan")

        if sensor.status != SensorStatus.PENDING:
            raise ValueError("Device sudah pernah disetujui")

        approved = sensor_crud.approve_device(
            self.db,
            sensor=sensor,
            silo_id=data.silo_id,
            nama=data.nama,
            tipe=data.tipe,
        )
        notification_crud.create(
            self.db,
            user_id=silo.peternakan.user_id,
            title="Perangkat berhasil dihubungkan",
            message=f"{data.nama} sekarang aktif pada silo {silo.nama}.",
            notification_type=NotificationType.INFO,
            category=NotificationCategory.DEVICE,
        )
        return approved
