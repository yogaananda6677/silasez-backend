from uuid import UUID

from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.crud import peternakan as peternakan_crud
from app.crud import silo as silo_crud
from app.crud.chat_room import chat_room as chat_room_crud
from app.models.peternakan import Peternakan
from app.models.silo import Silo
from app.models.sensor import Sensor
from app.models.sensor_log import SensorLog
from app.models.user import User
from app.schemas.silo import SiloCreateRequest, SiloUpdateRequest


class SiloService:

    def __init__(self, db: Session):
        self.db = db

    def _get_peternakan_or_404(self, peternakan_id: UUID) -> Peternakan:
        peternakan = peternakan_crud.get_by_id(self.db, peternakan_id)

        if peternakan is None:
            raise ValueError("Peternakan tidak ditemukan.")

        return peternakan

    def _assert_owner(self, user: User, peternakan: Peternakan) -> None:
        if user.role == UserRole.ADMIN:
            return
        if peternakan.user_id != user.id:
            raise PermissionError("Anda tidak memiliki akses ke peternakan ini.")

    def _assert_can_read(self, user: User, peternakan: Peternakan) -> None:
        if user.role == UserRole.ADMIN or peternakan.user_id == user.id:
            return

        if user.role == UserRole.PAKAR and chat_room_crud.has_consulted(
            self.db,
            pakar_id=user.id,
            peternak_id=peternakan.user_id,
        ):
            return

        raise PermissionError("Anda tidak memiliki akses ke peternakan ini.")

    def create(self, user: User, peternakan_id: UUID, data: SiloCreateRequest) -> Silo:
        peternakan = self._get_peternakan_or_404(peternakan_id)
        self._assert_owner(user, peternakan)

        return silo_crud.create_silo(
            self.db,
            peternakan_id=peternakan.id,
            nama=data.nama,
            kapasitas=data.kapasitas,
        )

    def list_for_peternakan(self, user: User, peternakan_id: UUID) -> list[Silo]:
        peternakan = self._get_peternakan_or_404(peternakan_id)
        self._assert_can_read(user, peternakan)

        return silo_crud.list_by_peternakan(self.db, peternakan_id)

    def get_readable(self, user: User, silo_id: UUID) -> Silo:
        silo = silo_crud.get_by_id(self.db, silo_id)

        if silo is None:
            raise ValueError("Silo tidak ditemukan.")

        self._assert_can_read(user, silo.peternakan)

        return silo

    def get_latest_sensor_reading(self, user: User, silo_id: UUID) -> dict | None:
        silo = self.get_readable(user, silo_id)
        latest = (
            self.db.query(SensorLog, Sensor)
            .join(Sensor, SensorLog.sensor_id == Sensor.id)
            .filter(Sensor.silo_id == silo.id)
            .order_by(SensorLog.created_at.desc())
            .first()
        )
        if latest is None:
            return None

        log, sensor = latest
        return {
            "id": log.id,
            "sensor_id": sensor.id,
            "device_id": sensor.device_id,
            "sensor_nama": sensor.nama,
            "silo_id": silo.id,
            "temperature": log.temperature,
            "water_content": log.water_content,
            "ph": log.ph,
            "delta_gas": log.delta_gas,
            "fermentation_day": log.fermentation_day,
            "phase": log.phase,
            "classification": log.classification,
            "recorded_at": log.created_at,
        }

    def update(self, user: User, silo_id: UUID, data: SiloUpdateRequest) -> Silo:
        silo = silo_crud.get_by_id(self.db, silo_id)

        if silo is None:
            raise ValueError("Silo tidak ditemukan.")

        self._assert_owner(user, silo.peternakan)

        updates = data.model_dump(exclude_unset=True, exclude_none=True)

        if updates:
            silo_crud.update_silo(self.db, silo, **updates)
        else:
            self.db.commit()
            self.db.refresh(silo)

        return silo

    def delete(self, user: User, silo_id: UUID) -> Silo:
        silo = silo_crud.get_by_id(self.db, silo_id)

        if silo is None:
            raise ValueError("Silo tidak ditemukan.")

        self._assert_owner(user, silo.peternakan)

        return silo_crud.soft_delete_silo(self.db, silo)
