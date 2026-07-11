from app.core.database import SessionLocal
from app.core.enums import NotificationType, SensorStatus, UserRole
from app.crud import sensor as sensor_crud
from app.crud import sensor_log as sensor_log_crud
from app.crud import notification as notification_crud
from app.models.user import User
from app.websocket.manager import manager


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
                )
            print(f"MQTT: Device baru terdeteksi, didaftarkan sebagai PENDING -> {device_id}")

        if jenis == "sensor":
            if sensor.status != SensorStatus.ACTIVE:
                print(
                    f"MQTT: Data dari '{device_id}' diabaikan "
                    f"(status masih '{sensor.status.value}', menunggu approval admin)"
                )
                return

            log = sensor_log_crud.create_log(
                db,
                sensor_id=sensor.id,
                temperature=payload.get("suhu", 0),
                humidity=payload.get("kadar_air", 0),
                ph=payload.get("ph", 0),
                # TODO: MQ135 di firmware saat ini cuma kasih satu nilai gabungan
                # (delta_gas), belum dipisah methane/ammonia/co2. Sementara
                # disimpan di 'methane', ammonia & co2 default 0 sampai
                # sensor gas terpisah tersedia.
                methane=payload.get("delta_gas", 0),
                ammonia=0,
                co2=0,
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
