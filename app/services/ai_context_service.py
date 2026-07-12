from datetime import datetime, timezone

from sqlalchemy.orm import Session, selectinload

from app.core.enums import FermentationStatus, UserRole
from app.models.peternakan import Peternakan
from app.models.sensor import Sensor
from app.models.sensor_log import SensorLog
from app.models.silo import Silo
from app.models.user import User


class AIContextService:
    """Menyusun konteks Gemini dari data milik user yang terautentikasi.

    Query selalu dimulai dari `Peternakan.user_id == user.id`, sehingga
    data peternak lain tidak mungkin masuk hanya karena ID disebutkan di
    pertanyaan. Batas jumlah farm/silo menjaga ukuran prompt tetap wajar.
    """

    MAX_FARMS = 5
    MAX_SILOS_PER_FARM = 8
    MAX_TEXT_LENGTH = 200

    def __init__(self, db: Session):
        self.db = db

    def build_for_peternak(self, user: User) -> dict:
        if user.role != UserRole.PETERNAK:
            raise PermissionError("Konteks AI hanya tersedia untuk peternak.")
        farms = (
            self.db.query(Peternakan)
            .options(
                selectinload(Peternakan.silos).selectinload(Silo.sensors),
                selectinload(Peternakan.silos).selectinload(Silo.fermentation_cycles),
            )
            .filter(
                Peternakan.user_id == user.id,
                Peternakan.is_deleted.is_(False),
            )
            .order_by(Peternakan.created_at.desc())
            .limit(self.MAX_FARMS)
            .all()
        )

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "scope": "authenticated_user_only",
            "user": {
                "fullname": self._text(user.fullname),
                "role": user.role.value,
            },
            "peternakan": [self._farm(farm) for farm in farms],
            "limitations": {
                "max_peternakan": self.MAX_FARMS,
                "max_silo_per_peternakan": self.MAX_SILOS_PER_FARM,
                "sensor_data": "latest_reading_only",
            },
        }

    def _farm(self, farm: Peternakan) -> dict:
        silos = [silo for silo in farm.silos if not silo.is_deleted]
        return {
            "nama": self._text(farm.nama),
            "alamat": self._text(farm.alamat),
            "jenis_ternak": self._text(farm.jenis_ternak),
            "jumlah_ternak": farm.jumlah_ternak,
            "jenis_pakan": self._text(farm.jenis_pakan),
            "silos": [
                self._silo(silo)
                for silo in silos[: self.MAX_SILOS_PER_FARM]
            ],
        }

    def _silo(self, silo: Silo) -> dict:
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
        latest = (
            self.db.query(SensorLog, Sensor)
            .join(Sensor, SensorLog.sensor_id == Sensor.id)
            .filter(Sensor.silo_id == silo.id)
            .order_by(SensorLog.created_at.desc())
            .first()
        )

        return {
            "nama": self._text(silo.nama),
            "kapasitas_kg": silo.kapasitas,
            "status": silo.status.value,
            "jumlah_sensor": len(silo.sensors),
            "fermentasi_aktif": None
            if active_cycle is None
            else {
                "tanggal_mulai": active_cycle.start_date.isoformat(),
                "tanggal_rencana_selesai": active_cycle.end_date.isoformat(),
                "hari_ke": active_cycle.current_day,
                "durasi_rencana_hari": active_cycle.planned_duration_days,
                "terlambat": active_cycle.is_overdue,
                "catatan": self._text(active_cycle.catatan),
            },
            "pembacaan_sensor_terbaru": None
            if latest is None
            else {
                "nama_sensor": self._text(latest[1].nama),
                "suhu_celsius": latest[0].temperature,
                "kadar_air_persen": latest[0].water_content,
                "ph": latest[0].ph,
                "delta_gas": latest[0].delta_gas,
                "fase": latest[0].phase,
                "klasifikasi": latest[0].classification,
                "direkam_pada": latest[0].created_at.isoformat(),
            },
        }

    def _text(self, value: str | None) -> str | None:
        if value is None:
            return None
        # Hilangkan karakter kontrol dan batasi input bebas pengguna agar
        # tidak mendominasi prompt atau menyisipkan payload sangat panjang.
        cleaned = " ".join(value.split())
        return cleaned[: self.MAX_TEXT_LENGTH]
