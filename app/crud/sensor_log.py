from uuid import UUID

from sqlalchemy.orm import Session

from app.models.sensor_log import SensorLog


def create_log(
    db: Session,
    sensor_id: UUID,
    temperature: float,
    water_content: float,
    ph: float,
    delta_gas: float,
    fermentation_cycle_id: UUID | None = None,
    fermentation_day: int | None = None,
    phase: str = "monitoring",
    classification: str | None = None,
) -> SensorLog:

    log = SensorLog(
        sensor_id=sensor_id,
        fermentation_cycle_id=fermentation_cycle_id,
        temperature=temperature,
        humidity=water_content,
        ph=ph,
        methane=delta_gas,
        ammonia=0,
        co2=0,
        fermentation_day=fermentation_day,
        phase=phase,
        classification=classification,
    )

    db.add(log)
    db.commit()
    db.refresh(log)

    return log


def get_latest(db: Session, sensor_id: UUID) -> SensorLog | None:
    return (
        db.query(SensorLog)
        .filter(SensorLog.sensor_id == sensor_id)
        .order_by(SensorLog.created_at.desc())
        .first()
    )


def has_monitoring_log_for_cycle(db: Session, cycle_id: UUID) -> bool:
    return (
        db.query(SensorLog.id)
        .filter(
            SensorLog.fermentation_cycle_id == cycle_id,
            SensorLog.phase == "monitoring",
        )
        .first()
        is not None
    )
