from uuid import UUID

from sqlalchemy.orm import Session

from app.core.enums import SensorStatus
from app.models.sensor import Sensor


def get_by_device_id(
    db: Session,
    device_id: str,
) -> Sensor | None:
    return (
        db.query(Sensor)
        .filter(Sensor.device_id == device_id)
        .first()
    )


def get_by_id(
    db: Session,
    sensor_id: UUID,
) -> Sensor | None:
    return (
        db.query(Sensor)
        .filter(Sensor.id == sensor_id)
        .first()
    )


def register_pending_device(
    db: Session,
    device_id: str,
    tipe: str = "esp32",
) -> Sensor:
    """
    Dipanggil otomatis oleh MQTT handler saat device_id baru pertama kali
    mengirim data tapi belum terdaftar di database. Sensor dibuat dengan
    status PENDING dan silo_id kosong sampai admin approve lewat aplikasi.
    """

    sensor = Sensor(
        device_id=device_id,
        nama=f"Device Baru ({device_id})",
        tipe=tipe,
        status=SensorStatus.PENDING,
        silo_id=None,
    )

    db.add(sensor)
    db.commit()
    db.refresh(sensor)

    return sensor


def list_pending(
    db: Session,
) -> list[Sensor]:
    return (
        db.query(Sensor)
        .filter(Sensor.status == SensorStatus.PENDING)
        .order_by(Sensor.created_at.desc())
        .all()
    )


def approve_device(
    db: Session,
    sensor: Sensor,
    silo_id: UUID,
    nama: str,
    tipe: str,
) -> Sensor:
    sensor.silo_id = silo_id
    sensor.nama = nama
    sensor.tipe = tipe
    sensor.status = SensorStatus.ACTIVE

    db.commit()
    db.refresh(sensor)

    return sensor
