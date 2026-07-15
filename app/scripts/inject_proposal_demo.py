"""Create an isolated 21-day SilaseZ proposal demo fixture.

Run inside the backend container. The command is idempotent: an existing
fixture is reused and readings at the same cycle/day/time are updated.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

import app.models  # noqa: F401 - register every SQLAlchemy model
from app.core.database import SessionLocal
from app.core.enums import FermentationStatus, SensorStatus, SiloStatus, UserRole
from app.core.security import hash_password
from app.models.fermentation_cycle import FermentationCycle
from app.models.lokasi import Lokasi
from app.models.peternakan import Peternakan
from app.models.sensor import Sensor
from app.models.sensor_log import SensorLog
from app.models.silo import Silo
from app.models.user import User


JAKARTA = ZoneInfo("Asia/Jakarta")


@dataclass(frozen=True)
class DemoReading:
    day: int
    at: time
    temperature: float
    water_content: float
    ph: float
    delta_gas: float
    output: str


def _r(day, hour, temperature, water, ph, gas, output):
    return DemoReading(day, time(hour), temperature, water, ph, gas, output)


READINGS = (
    _r(1, 8, 28.5, 92.8, 7.82, 38, "Proses Awal"),
    _r(1, 16, 30.2, 92.5, 7.78, 45, "Proses Awal"),
    _r(2, 8, 29.8, 92.2, 7.72, 52, "Proses Awal"),
    _r(2, 16, 31.5, 92.0, 7.65, 63, "Proses Awal"),
    _r(3, 8, 33.2, 91.5, 7.44, 79, "Proses Awal"),
    _r(3, 16, 34.8, 91.2, 7.38, 88, "Proses Awal"),
    _r(4, 8, 34.5, 91.0, 7.18, 105, "Fermentasi perlu diwaspadai"),
    _r(4, 16, 35.8, 90.8, 7.08, 122, "Fermentasi perlu diwaspadai"),
    _r(5, 8, 33.5, 90.5, 6.78, 145, "Fermentasi Berlangsung"),
    _r(5, 16, 34.2, 90.2, 6.62, 162, "Fermentasi Berlangsung"),
    _r(6, 8, 31.8, 90.0, 6.25, 182, "Fermentasi Berlangsung"),
    _r(6, 16, 32.8, 89.8, 6.10, 198, "Fermentasi Berlangsung"),
    _r(7, 8, 30.2, 89.5, 5.68, 228, "Fermentasi Berlangsung"),
    _r(7, 16, 31.0, 89.3, 5.52, 245, "Fermentasi Berlangsung"),
    _r(8, 8, 29.5, 89.0, 5.15, 282, "Fermentasi Berlangsung"),
    _r(8, 16, 30.5, 89.2, 4.98, 298, "Fermentasi Berlangsung"),
    _r(9, 8, 28.8, 88.5, 4.72, 325, "Fermentasi Berlangsung"),
    _r(9, 16, 29.8, 88.8, 4.58, 345, "Fermentasi Berlangsung"),
    _r(10, 8, 28.5, 88.2, 4.42, 368, "Fermentasi Berlangsung"),
    _r(10, 16, 29.2, 88.0, 4.35, 388, "Fermentasi Berlangsung"),
    _r(11, 8, 27.9, 87.8, 4.25, 395, "Fermentasi Sukses"),
    _r(11, 16, 28.8, 87.5, 4.18, 405, "Fermentasi Sukses"),
    _r(12, 8, 27.5, 87.3, 4.12, 415, "Fermentasi Sukses"),
    _r(12, 16, 34.5, 87.2, 5.82, 512, "Fermentasi perlu diwaspadai"),
    _r(13, 8, 28.5, 87.0, 4.22, 385, "Fermentasi Sukses"),
    _r(13, 16, 29.2, 86.8, 4.18, 362, "Fermentasi Sukses"),
    _r(14, 8, 27.8, 86.5, 4.15, 342, "Fermentasi Sukses"),
    _r(14, 16, 28.5, 86.3, 4.12, 325, "Fermentasi Sukses"),
    _r(15, 8, 27.5, 86.1, 4.10, 308, "Fermentasi Sukses"),
    _r(15, 16, 28.2, 85.9, 4.08, 292, "Fermentasi Sukses"),
    _r(16, 8, 27.2, 85.7, 4.08, 278, "Fermentasi Sukses"),
    _r(16, 16, 27.8, 85.5, 4.07, 265, "Fermentasi Sukses"),
    _r(17, 8, 27.0, 85.3, 4.07, 252, "Fermentasi Sukses"),
    _r(17, 16, 27.5, 85.2, 4.06, 242, "Fermentasi Sukses"),
    _r(18, 8, 26.9, 85.0, 4.06, 228, "Fermentasi Sukses"),
    _r(18, 16, 27.4, 84.9, 4.05, 215, "Fermentasi Sukses"),
    _r(19, 8, 26.8, 84.8, 4.05, 205, "Fermentasi Sukses"),
    _r(19, 16, 27.2, 84.7, 4.04, 195, "Fermentasi Sukses"),
    _r(20, 8, 26.7, 84.6, 4.04, 182, "Fermentasi Sukses"),
    _r(20, 16, 27.0, 84.5, 4.03, 172, "Fermentasi Sukses"),
    _r(21, 8, 26.5, 84.5, 4.02, 158, "Fermentasi Sukses"),
    _r(21, 16, 26.8, 84.4, 4.01, 148, "Fermentasi Sukses"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", default="proposal.testing@silasez.com")
    parser.add_argument("--password", required=True)
    parser.add_argument("--fullname", default="Peternak Demo Proposal")
    parser.add_argument("--phone", default="081200002126")
    parser.add_argument("--start-date", type=date.fromisoformat, default=date(2026, 6, 22))
    parser.add_argument("--reset-password", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def _fixture(db: Session, args: argparse.Namespace):
    user = db.query(User).filter(User.email == args.email).first()
    if user is None:
        user = User(
            fullname=args.fullname,
            email=args.email,
            phone=args.phone,
            password=hash_password(args.password),
            role=UserRole.PETERNAK,
            is_active=True,
        )
        db.add(user)
        db.flush()
    elif args.reset_password:
        user.password = hash_password(args.password)
        user.is_active = True

    farm = db.query(Peternakan).filter(
        Peternakan.user_id == user.id,
        Peternakan.nama == "Peternakan Demo Proposal",
        Peternakan.is_deleted.is_(False),
    ).first()
    if farm is None:
        location = Lokasi(
            latitude=-7.2575,
            longitude=112.7521,
            provinsi="Jawa Timur",
            kabupaten="Kota Surabaya",
            kecamatan="Demo",
            desa="Demo Proposal",
            alamat_lengkap="Lokasi simulasi untuk demonstrasi proposal SilaseZ",
        )
        db.add(location)
        db.flush()
        farm = Peternakan(
            user_id=user.id,
            lokasi_id=location.id,
            nama="Peternakan Demo Proposal",
            alamat="Surabaya, Jawa Timur",
            jenis_ternak="Sapi",
            jumlah_ternak=25,
            jenis_pakan="Silase Jagung",
        )
        db.add(farm)
        db.flush()

    silo = db.query(Silo).filter(
        Silo.peternakan_id == farm.id,
        Silo.nama == "Silo Demo Fermentasi 21 Hari",
        Silo.is_deleted.is_(False),
    ).first()
    if silo is None:
        silo = Silo(
            peternakan_id=farm.id,
            nama="Silo Demo Fermentasi 21 Hari",
            kapasitas=1000,
            status=SiloStatus.ACTIVE,
        )
        db.add(silo)
        db.flush()

    sensor = db.query(Sensor).filter(Sensor.device_id == "SIM-PROPOSAL-21D").first()
    if sensor is None:
        sensor = Sensor(
            silo_id=silo.id,
            device_id="SIM-PROPOSAL-21D",
            nama="Sensor Simulasi Proposal",
            tipe="simulator",
            status=SensorStatus.ACTIVE,
        )
        db.add(sensor)
        db.flush()
    elif sensor.silo_id != silo.id:
        raise RuntimeError("SIM-PROPOSAL-21D sudah terhubung ke silo lain.")

    cycle = db.query(FermentationCycle).filter(
        FermentationCycle.silo_id == silo.id,
        FermentationCycle.start_date == args.start_date,
    ).first()
    if cycle is None:
        cycle = FermentationCycle(
            silo_id=silo.id,
            started_by=user.id,
            start_date=args.start_date,
            planned_duration_days=21,
            end_date=args.start_date + timedelta(days=20),
            status=FermentationStatus.RUNNING,
            catatan="Data simulasi proposal: 2 pembacaan per hari selama 21 hari.",
        )
        db.add(cycle)
        db.flush()
    else:
        cycle.planned_duration_days = 21
        cycle.end_date = args.start_date + timedelta(days=20)
        cycle.status = FermentationStatus.RUNNING
        cycle.actual_end_date = None

    return user, farm, silo, sensor, cycle


def inject(db: Session, args: argparse.Namespace) -> dict:
    user, farm, silo, sensor, cycle = _fixture(db, args)
    inserted = 0
    updated = 0

    for reading in READINGS:
        recorded_at = datetime.combine(
            args.start_date + timedelta(days=reading.day - 1),
            reading.at,
            tzinfo=JAKARTA,
        )
        log = db.query(SensorLog).filter(
            SensorLog.sensor_id == sensor.id,
            SensorLog.fermentation_cycle_id == cycle.id,
            SensorLog.fermentation_day == reading.day,
            SensorLog.created_at == recorded_at,
        ).first()
        if log is None:
            log = SensorLog(
                sensor_id=sensor.id,
                fermentation_cycle_id=cycle.id,
                created_at=recorded_at,
                updated_at=recorded_at,
                fermentation_day=reading.day,
                phase="fermentation",
                temperature=reading.temperature,
                humidity=reading.water_content,
                ph=reading.ph,
                methane=reading.delta_gas,
                ammonia=0,
                co2=0,
                classification=reading.output,
            )
            db.add(log)
            inserted += 1
        else:
            log.temperature = reading.temperature
            log.humidity = reading.water_content
            log.ph = reading.ph
            log.methane = reading.delta_gas
            log.classification = reading.output
            updated += 1

    db.flush()
    return {
        "email": user.email,
        "peternakan_id": str(farm.id),
        "silo_id": str(silo.id),
        "device_id": sensor.device_id,
        "cycle_id": str(cycle.id),
        "start_date": str(cycle.start_date),
        "end_date": str(cycle.end_date),
        "inserted": inserted,
        "updated": updated,
        "total": len(READINGS),
    }


def main() -> None:
    args = parse_args()
    if len(READINGS) != 42 or {item.day for item in READINGS} != set(range(1, 22)):
        raise RuntimeError("Dataset harus berisi 42 pembacaan untuk hari 1-21.")

    db = SessionLocal()
    try:
        result = inject(db, args)
        if args.dry_run:
            db.rollback()
            result["mode"] = "dry-run (rolled back)"
        else:
            db.commit()
            result["mode"] = "committed"
        print(result)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
