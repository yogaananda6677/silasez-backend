from uuid import UUID

from sqlalchemy.orm import Session

from app.models.silo import Silo


def create_silo(
    db: Session,
    *,
    peternakan_id: UUID,
    nama: str,
    kapasitas: int,
) -> Silo:

    silo = Silo(
        peternakan_id=peternakan_id,
        nama=nama,
        kapasitas=kapasitas,
    )

    db.add(silo)
    db.commit()
    db.refresh(silo)

    return silo


def get_by_id(
    db: Session,
    silo_id: UUID,
) -> Silo | None:

    return (
        db.query(Silo)
        .filter(
            Silo.id == silo_id,
            Silo.is_deleted.is_(False),
        )
        .first()
    )


def list_by_peternakan(
    db: Session,
    peternakan_id: UUID,
) -> list[Silo]:

    return (
        db.query(Silo)
        .filter(
            Silo.peternakan_id == peternakan_id,
            Silo.is_deleted.is_(False),
        )
        .order_by(Silo.created_at.desc())
        .all()
    )


def update_silo(
    db: Session,
    silo: Silo,
    **fields,
) -> Silo:

    for key, value in fields.items():
        setattr(silo, key, value)

    db.commit()
    db.refresh(silo)

    return silo


def soft_delete_silo(
    db: Session,
    silo: Silo,
) -> Silo:

    silo.is_deleted = True

    db.commit()
    db.refresh(silo)

    return silo
