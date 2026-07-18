from uuid import UUID

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from statistics import mean

from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.crud import peternakan as peternakan_crud
from app.crud import silo as silo_crud
from app.crud.chat_room import chat_room as chat_room_crud
from app.models.peternakan import Peternakan
from app.models.fermentation_cycle import FermentationCycle
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
            .filter(
                Sensor.silo_id == silo.id,
                SensorLog.created_at <= datetime.now(timezone.utc),
            )
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

    def get_sensor_chart(
        self,
        user: User,
        silo_id: UUID,
        day_from: int,
        day_to: int,
        selected_day: int | None,
        fermentation_cycle_id: UUID | None,
    ) -> dict:
        silo = self.get_readable(user, silo_id)

        cycle_query = self.db.query(FermentationCycle).filter(
            FermentationCycle.silo_id == silo.id
        )
        if fermentation_cycle_id is not None:
            cycle = cycle_query.filter(
                FermentationCycle.id == fermentation_cycle_id
            ).first()
        else:
            cycle = cycle_query.order_by(
                FermentationCycle.start_date.desc(),
                FermentationCycle.created_at.desc(),
            ).first()

        if cycle is None:
            raise ValueError("Siklus fermentasi tidak ditemukan pada silo ini.")
        if day_from > day_to:
            raise ValueError("day_from tidak boleh lebih besar dari day_to.")

        rows = (
            self.db.query(SensorLog, Sensor)
            .join(Sensor, SensorLog.sensor_id == Sensor.id)
            .filter(
                Sensor.silo_id == silo.id,
                SensorLog.fermentation_cycle_id == cycle.id,
                SensorLog.fermentation_day.between(1, cycle.planned_duration_days),
            )
            .order_by(SensorLog.created_at.asc())
            .all()
        )

        by_day: dict[int, list[tuple[SensorLog, Sensor]]] = defaultdict(list)
        for log, sensor in rows:
            if log.fermentation_day is not None:
                by_day[log.fermentation_day].append((log, sensor))

        chart = [
            self._build_chart_point(cycle, day, by_day[day])
            for day in range(day_from, day_to + 1)
            if by_day[day]
        ]
        selected_rows = by_day.get(selected_day, []) if selected_day else []

        return {
            "silo_id": silo.id,
            "fermentation_cycle_id": cycle.id,
            "start_date": cycle.start_date,
            "end_date": cycle.end_date,
            "planned_duration_days": cycle.planned_duration_days,
            "current_day": cycle.current_day,
            "day_from": day_from,
            "day_to": day_to,
            "selected_day": selected_day,
            "timeline": [
                {
                    "day": day,
                    "date": cycle.start_date + timedelta(days=day - 1),
                    "has_data": bool(by_day[day]),
                    "reading_count": len(by_day[day]),
                    "selected": day == selected_day,
                }
                for day in range(1, cycle.planned_duration_days + 1)
            ],
            "chart": chart,
            "selected_day_readings": [
                self._serialize_chart_reading(log, sensor)
                for log, sensor in selected_rows
            ],
            "analysis": self._build_chart_analysis(chart, selected_rows),
        }

    @staticmethod
    def _build_chart_point(cycle, day: int, rows: list[tuple[SensorLog, Sensor]]) -> dict:
        logs = [log for log, _ in rows]
        classifications = [log.classification for log in logs if log.classification]

        def stats(attribute: str) -> tuple[float, float, float]:
            values = [float(getattr(log, attribute)) for log in logs]
            return round(mean(values), 2), round(min(values), 2), round(max(values), 2)

        temperature = stats("temperature")
        water_content = stats("water_content")
        ph = stats("ph")
        delta_gas = stats("delta_gas")
        return {
            "day": day,
            "date": cycle.start_date + timedelta(days=day - 1),
            "reading_count": len(logs),
            "temperature_avg": temperature[0],
            "temperature_min": temperature[1],
            "temperature_max": temperature[2],
            "water_content_avg": water_content[0],
            "water_content_min": water_content[1],
            "water_content_max": water_content[2],
            "ph_avg": ph[0],
            "ph_min": ph[1],
            "ph_max": ph[2],
            "delta_gas_avg": delta_gas[0],
            "delta_gas_min": delta_gas[1],
            "delta_gas_max": delta_gas[2],
            "classification": Counter(classifications).most_common(1)[0][0]
            if classifications else None,
        }

    @staticmethod
    def _serialize_chart_reading(log: SensorLog, sensor: Sensor) -> dict:
        return {
            "id": log.id,
            "sensor_id": sensor.id,
            "device_id": sensor.device_id,
            "sensor_nama": sensor.nama,
            "temperature": log.temperature,
            "water_content": log.water_content,
            "ph": log.ph,
            "delta_gas": log.delta_gas,
            "classification": log.classification,
            "recorded_at": log.created_at,
        }

    @staticmethod
    def _build_chart_analysis(chart: list[dict], selected_rows) -> dict:
        source = chart

        def trend(field: str, tolerance: float) -> str:
            if len(source) < 2:
                return "belum_cukup_data"
            difference = source[-1][field] - source[0][field]
            if abs(difference) <= tolerance:
                return "stabil"
            return "naik" if difference > 0 else "turun"

        classifications = [
            log.classification for log, _ in selected_rows if log.classification
        ] or [point["classification"] for point in chart if point["classification"]]

        if any(value == "Fermentasi Gagal" for value in classifications):
            status = "perlu_perhatian"
            summary = "Pembacaan menunjukkan klasifikasi fermentasi gagal."
            suggestions = [
                "Periksa kondisi bahan dan silo secara langsung.",
                "Konsultasikan hasil pembacaan dengan pakar sebelum silase digunakan.",
            ]
        elif any(value == "Fermentasi perlu diwaspadai" for value in classifications):
            status = "perlu_perhatian"
            summary = "Ada pembacaan yang perlu diwaspadai pada rentang terpilih."
            suggestions = [
                "Periksa kerapatan dan kebocoran silo.",
                "Pantau perubahan suhu, pH, kadar air, dan gas pada pembacaan berikutnya.",
            ]
        elif chart:
            status = "baik"
            summary = "Data tersedia dan tidak menunjukkan klasifikasi berbahaya."
            suggestions = ["Lanjutkan monitoring sesuai jadwal dan amati perubahan tren."]
        else:
            status = "belum_ada_data"
            summary = "Belum ada pembacaan sensor pada rentang yang dipilih."
            suggestions = ["Pastikan sensor aktif dan mengirim data ke backend."]

        return {
            "status": status,
            "ringkasan": summary,
            "saran": suggestions,
            "temperature_trend": trend("temperature_avg", 0.2),
            "water_content_trend": trend("water_content_avg", 0.5),
            "ph_trend": trend("ph_avg", 0.1),
            "delta_gas_trend": trend("delta_gas_avg", 5.0),
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
