from datetime import date, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.enums import FermentationStatus
from app.models.fermentation_cycle import FermentationCycle
from app.models.silo import Silo


def create(
    db: Session,
    *,
    silo_id: UUID,
    started_by: UUID,
    start_date: date,
    planned_duration_days: int,
    catatan: str | None,
) -> FermentationCycle:

    cycle = FermentationCycle(
        silo_id=silo_id,
        started_by=started_by,
        start_date=start_date,
        planned_duration_days=planned_duration_days,
        # Hari pertama ikut dihitung, jadi periode 21 hari berakhir pada
        # start_date + 20 hari (bukan masuk hari ke-22).
        end_date=start_date + timedelta(days=planned_duration_days - 1),
        catatan=catatan,
        status=FermentationStatus.RUNNING,
    )

    db.add(cycle)
    db.commit()
    db.refresh(cycle)

    return cycle


def get_by_id(
    db: Session,
    cycle_id: UUID,
) -> FermentationCycle | None:

    return (
        db.query(FermentationCycle)
        .filter(FermentationCycle.id == cycle_id)
        .first()
    )


def get_active_by_silo(
    db: Session,
    silo_id: UUID,
) -> FermentationCycle | None:

    return (
        db.query(FermentationCycle)
        .filter(
            FermentationCycle.silo_id == silo_id,
            FermentationCycle.status == FermentationStatus.RUNNING,
        )
        .first()
    )


def list_by_silo(
    db: Session,
    silo_id: UUID,
) -> list[FermentationCycle]:

    return (
        db.query(FermentationCycle)
        .filter(FermentationCycle.silo_id == silo_id)
        .order_by(FermentationCycle.start_date.desc())
        .all()
    )


def list_active_by_peternakan(
    db: Session,
    peternakan_id: UUID,
) -> list[FermentationCycle]:
    """Semua siklus RUNNING lintas silo milik 1 peternakan — dipakai buat
    ringkasan dashboard yang mencakup banyak silo sekaligus."""

    return (
        db.query(FermentationCycle)
        .join(Silo, FermentationCycle.silo_id == Silo.id)
        .filter(
            Silo.peternakan_id == peternakan_id,
            Silo.is_deleted.is_(False),
            FermentationCycle.status == FermentationStatus.RUNNING,
        )
        .all()
    )


def finish(
    db: Session,
    cycle: FermentationCycle,
    *,
    status: FermentationStatus,
    catatan: str | None,
) -> FermentationCycle:

    cycle.status = status
    cycle.actual_end_date = date.today()

    if catatan is not None:
        cycle.catatan = catatan

    db.commit()
    db.refresh(cycle)

    return cycle


def finish_expired(db: Session, cycle: FermentationCycle) -> FermentationCycle:
    """Tutup otomatis periode fermentasi tepat di akhir hari ke-21."""
    cycle.status = FermentationStatus.COMPLETED
    cycle.actual_end_date = cycle.end_date
    db.commit()
    db.refresh(cycle)
    return cycle
