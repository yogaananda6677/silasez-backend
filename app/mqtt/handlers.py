from app.core.database import SessionLocal
from app.core.enums import (
    NotificationCategory,
    NotificationType,
    SensorStatus,
    UserRole,
)
from app.crud import sensor as sensor_crud
from app.crud import fermentation_cycle as cycle_crud
from app.crud import sensor_log as sensor_log_crud
from app.crud import notification as notification_crud
from app.models.user import User
from app.websocket.manager import manager


_CLASSIFICATION_ALIASES = {
    "Proses Awal": "Proses Awal",
    "Fermentasi Berlangsung": "Fermentasi Berlangsung",
    "Fermentasi Ideal": "Fermentasi Sukses",
    "Fermentasi Sukses": "Fermentasi Sukses",
    "Fermentasi Perlu Diwaspadai": "Fermentasi perlu diwaspadai",
    "Fermentasi perlu diwaspadai": "Fermentasi perlu diwaspadai",
    "Fermentasi Gagal": "Fermentasi Gagal",
}


def _classification_notification(classification: str):
    if classification == "Fermentasi Sukses":
        return NotificationType.INFO, "Fermentasi Sukses"
    if classification == "Fermentasi perlu diwaspadai":
        return NotificationType.WARNING, "Fermentasi perlu diwaspadai"
    if classification == "Fermentasi Gagal":
        return NotificationType.DANGER, "Fermentasi Gagal"
    return None


def handle_message(
    topic: str,
    payload: dict,
):
    # Format topic wajib: silasez/device/{device_id}/{status|sensor}
    parts = topic.split("/")

    if len(parts) != 4 or parts[0] != "silasez" or parts[1] != "device":
        print(f"MQTT: topic tidak dikenali, diabaikan: {topic}")
        return

    device_id = parts[2]
    jenis = parts[3]

    db = SessionLocal()

    try:
        sensor = sensor_crud.get_by_device_id(db, device_id)

        # Device belum pernah terlihat -> auto-register sebagai PENDING,
        # menunggu admin assign ke silo & approve lewat aplikasi.
        if sensor is None:
            sensor = sensor_crud.register_pending_device(db, device_id)
            admins = db.query(User).filter(
                User.role == UserRole.ADMIN,
                User.is_active.is_(True),
                User.is_deleted.is_(False),
            ).all()
            for admin in admins:
                notification_crud.create(
                    db,
                    user_id=admin.id,
                    title="Perangkat baru menunggu approval",
                    message=f"Device {device_id} terdeteksi dan belum terhubung ke silo.",
                    notification_type=NotificationType.INFO,
                    category=NotificationCategory.DEVICE,
                )
            print(f"MQTT: Device baru terdeteksi, didaftarkan sebagai PENDING -> {device_id}")

        if jenis == "sensor":
            if sensor.status != SensorStatus.ACTIVE:
                print(
                    f"MQTT: Data dari '{device_id}' diabaikan "
                    f"(status masih '{sensor.status.value}', menunggu approval admin)"
                )
                return

            previous = sensor_log_crud.get_latest(db, sensor.id)
            active_cycle = cycle_crud.get_active_by_silo(db, sensor.silo_id)
            fermentation_day = active_cycle.current_day if active_cycle else None
            phase = "fermentation" if active_cycle and fermentation_day <= 21 else "monitoring"
            classification = None

            if phase == "fermentation":
                classification = _CLASSIFICATION_ALIASES.get(payload.get("output"))
            elif active_cycle is not None and not sensor_log_crud.has_monitoring_log_for_cycle(
                db, active_cycle.id
            ):
                # Siklus tetap RUNNING sampai peternak menutupnya manual.
                # Alert hanya dibuat sekali saat pembacaan monitoring pertama.
                notification_crud.create(
                    db,
                    user_id=sensor.silo.peternakan.user_id,
                    title="Periode fermentasi 21 hari terlewati",
                    message=(
                        f"Silo {sensor.silo.nama} sudah memasuki hari ke-"
                        f"{fermentation_day}. Data masuk fase monitoring; "
                        "tutup siklus secara manual jika proses dinyatakan selesai."
                    ),
                    notification_type=NotificationType.WARNING,
                    category=NotificationCategory.FERMENTATION,
                )

            log = sensor_log_crud.create_log(
                db,
                sensor_id=sensor.id,
                fermentation_cycle_id=active_cycle.id if active_cycle else None,
                temperature=payload.get("suhu", 0),
                water_content=payload.get("kadar_air", 0),
                ph=payload.get("ph", 0),
                delta_gas=payload.get("delta_gas", 0),
                fermentation_day=fermentation_day,
                phase=phase,
                classification=classification,
            )

            alert = (
                _classification_notification(classification)
                if classification is not None
                else None
            )
            if alert and (previous is None or previous.classification != classification):
                notification_type, title = alert
                notification_crud.create(
                    db,
                    user_id=sensor.silo.peternakan.user_id,
                    title=title,
                    message=(
                        f"Silo {sensor.silo.nama} pada hari ke-{fermentation_day}: "
                        f"{classification}."
                    ),
                    notification_type=notification_type,
                    category=NotificationCategory.FERMENTATION,
                )

            # TODO: broadcast realtime ke frontend
            # await manager.broadcast({...})

        elif jenis == "status":
            print(f"MQTT status dari '{device_id}': {payload}")

        else:
            print(f"MQTT: jenis topic tidak dikenali '{jenis}' dari {device_id}")

    except Exception as e:
        db.rollback()
        print(f"MQTT handler error: {e}")

    finally:
        db.close()
