from uuid import UUID

from sqlalchemy.orm import Session

from app.models.sensor_log import SensorLog


def create_log(
    db: Session,
    sensor_id: UUID,
    temperature: float,
    humidity: float,
    ph: float,
    methane: float,
    ammonia: float,
    co2: float,
) -> SensorLog:

    log = SensorLog(
        sensor_id=sensor_id,
        temperature=temperature,
        humidity=humidity,
        ph=ph,
        methane=methane,
        ammonia=ammonia,
        co2=co2,
    )

    db.add(log)
    db.commit()
    db.refresh(log)

    return log
