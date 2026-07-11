from uuid import UUID

from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.enums import FermentationStatus, SensorStatus, SiloStatus, UserRole
from app.crud.chat_room import chat_room as chat_room_crud
from app.models.chat_room import ChatRoom
from app.models.fermentation_cycle import FermentationCycle
from app.models.peternakan import Peternakan
from app.models.sensor import Sensor
from app.models.sensor_log import SensorLog
from app.models.silo import Silo
from app.models.user import User


class PakarService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def require_pakar(user: User) -> None:
        if user.role != UserRole.PAKAR:
            raise PermissionError("Hanya pakar yang dapat mengakses endpoint ini.")

    def _base_peternakan_query(self):
        return (
            self.db.query(Peternakan)
            .options(
                joinedload(Peternakan.owner),
                joinedload(Peternakan.lokasi),
                selectinload(Peternakan.silos).selectinload(Silo.sensors),
                selectinload(Peternakan.silos).selectinload(Silo.fermentation_cycles),
            )
            .filter(Peternakan.is_deleted.is_(False))
        )

    def list_peternakan(self, user: User) -> list[dict]:
        self.require_pakar(user)

        farms = (
            self._base_peternakan_query()
            .filter(
                Peternakan.user_id.in_(
                    self.db.query(ChatRoom.peternak_id).filter(
                        ChatRoom.pakar_id == user.id,
                        ChatRoom.is_ai.is_(False),
                    )
                )
            )
            .order_by(Peternakan.created_at.desc())
            .all()
        )
        return [self._build_peternakan(user, farm, include_silos=False) for farm in farms]

    def get_peternakan(self, user: User, peternakan_id: UUID) -> dict:
        self.require_pakar(user)

        farm = self._base_peternakan_query().filter(Peternakan.id == peternakan_id).first()
        if farm is None:
            raise ValueError("Peternakan tidak ditemukan.")
        self._assert_can_access(user, farm)

        return self._build_peternakan(user, farm, include_silos=True)

    def get_history(
        self,
        user: User,
        peternakan_id: UUID,
        sensor_limit: int,
        fermentation_limit: int,
    ) -> dict:
        farm = (
            self.db.query(Peternakan)
            .filter(
                Peternakan.id == peternakan_id,
                Peternakan.is_deleted.is_(False),
            )
            .first()
        )
        if farm is None:
            raise ValueError("Peternakan tidak ditemukan.")
        self._assert_can_access(user, farm)

        logs = (
            self.db.query(SensorLog, Sensor, Silo)
            .join(Sensor, SensorLog.sensor_id == Sensor.id)
            .join(Silo, Sensor.silo_id == Silo.id)
            .filter(
                Silo.peternakan_id == peternakan_id,
                Silo.is_deleted.is_(False),
            )
            .order_by(SensorLog.created_at.desc())
            .limit(sensor_limit)
            .all()
        )

        cycles = (
            self.db.query(FermentationCycle)
            .join(Silo, FermentationCycle.silo_id == Silo.id)
            .options(joinedload(FermentationCycle.silo))
            .filter(
                Silo.peternakan_id == peternakan_id,
                Silo.is_deleted.is_(False),
            )
            .order_by(FermentationCycle.start_date.desc())
            .limit(fermentation_limit)
            .all()
        )

        return {
            "peternakan_id": peternakan_id,
            "sensor_logs": [self._serialize_log(log, sensor, silo) for log, sensor, silo in logs],
            "fermentation_cycles": cycles,
        }

    def _assert_can_access(self, user: User, farm: Peternakan) -> None:
        # Pemilik selalu boleh membaca data monitoring peternakan dan silo
        # miliknya sendiri. Admin juga tetap punya akses operasional.
        if farm.user_id == user.id or user.role == UserRole.ADMIN:
            return

        # Selain pemilik, hanya pakar yang pernah/sedang berkonsultasi
        # dengan pemilik peternakan ini yang boleh membaca riwayat.
        if user.role != UserRole.PAKAR:
            raise PermissionError("Anda tidak memiliki akses ke peternakan ini.")

        if not chat_room_crud.has_consulted(
            self.db,
            pakar_id=user.id,
            peternak_id=farm.user_id,
        ):
            raise PermissionError(
                "Anda tidak memiliki hubungan konsultasi dengan peternakan ini."
            )

    def _build_peternakan(
        self,
        user: User,
        farm: Peternakan,
        include_silos: bool,
    ) -> dict:
        silos = [silo for silo in farm.silos if not silo.is_deleted]
        silo_conditions = [self._build_silo_condition(silo) for silo in silos]

        latest_times = [
            item["pembacaan_terbaru"]["recorded_at"]
            for item in silo_conditions
            if item["pembacaan_terbaru"] is not None
        ]

        conditions = {item["kondisi"] for item in silo_conditions}
        if "perlu_perhatian" in conditions:
            condition = "perlu_perhatian"
        elif "aktif" in conditions:
            condition = "aktif"
        else:
            condition = "belum_ada_data"

        latest_readings = [
            item["pembacaan_terbaru"]
            for item in silo_conditions
            if item["pembacaan_terbaru"] is not None
        ]
        latest_reading = max(
            latest_readings,
            key=lambda item: item["recorded_at"],
            default=None,
        )
        room = chat_room_crud.get_pakar_room(
            self.db,
            peternak_id=farm.user_id,
            pakar_id=user.id,
        )

        result = {
            "id": farm.id,
            "nama": farm.nama,
            "alamat": farm.alamat,
            "jenis_ternak": farm.jenis_ternak,
            "jumlah_ternak": farm.jumlah_ternak,
            "jenis_pakan": farm.jenis_pakan,
            "owner": farm.owner,
            "lokasi": farm.lokasi,
            "jumlah_silo": len(silos),
            "kondisi": condition,
            "pembacaan_terakhir_at": max(latest_times) if latest_times else None,
            "pembacaan_terbaru": latest_reading,
            "chat_room_id": room.id,
        }
        if include_silos:
            result["silos"] = silo_conditions

        return result

    def _build_silo_condition(self, silo: Silo) -> dict:
        active_cycle = next(
            (
                cycle
                for cycle in sorted(
                    silo.fermentation_cycles,
                    key=lambda item: item.start_date,
                    reverse=True,
                )
                if cycle.status == FermentationStatus.RUNNING
            ),
            None,
        )
        latest = self._latest_log_for_silo(silo.id)
        sensor_statuses = [sensor.status for sensor in silo.sensors]

        needs_attention = (
            silo.status != SiloStatus.ACTIVE
            or any(status in (SensorStatus.OFFLINE, SensorStatus.ERROR) for status in sensor_statuses)
            or (active_cycle is not None and active_cycle.is_overdue)
        )
        if needs_attention:
            condition = "perlu_perhatian"
        elif latest is not None:
            condition = "aktif"
        else:
            condition = "belum_ada_data"

        return {
            "id": silo.id,
            "nama": silo.nama,
            "kapasitas": silo.kapasitas,
            "status": silo.status,
            "sensor_statuses": sensor_statuses,
            "kondisi": condition,
            "fermentasi_aktif": active_cycle,
            "pembacaan_terbaru": (
                self._serialize_log(latest[0], latest[1]) if latest is not None else None
            ),
        }

    def _latest_log_for_silo(self, silo_id: UUID):
        return (
            self.db.query(SensorLog, Sensor)
            .join(Sensor, SensorLog.sensor_id == Sensor.id)
            .filter(Sensor.silo_id == silo_id)
            .order_by(SensorLog.created_at.desc())
            .first()
        )

    @staticmethod
    def _serialize_log(log: SensorLog, sensor: Sensor, silo: Silo | None = None) -> dict:
        data = {
            "id": log.id,
            "sensor_id": sensor.id,
            "device_id": sensor.device_id,
            "sensor_nama": sensor.nama,
            "temperature": log.temperature,
            "humidity": log.humidity,
            "ph": log.ph,
            "methane": log.methane,
            "ammonia": log.ammonia,
            "co2": log.co2,
            "recorded_at": log.created_at,
        }
        if silo is not None:
            data.update({"silo_id": silo.id, "silo_nama": silo.nama})
        return data
