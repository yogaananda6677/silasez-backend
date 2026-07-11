from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.models.peternakan import Peternakan


def create_peternakan(
    db: Session,
    *,
    user_id: UUID,
    lokasi_id: UUID,
    nama: str,
    alamat: str | None,
    jenis_ternak: str,
    jumlah_ternak: int,
    jenis_pakan: str,
) -> Peternakan:
    peternakan = Peternakan(
        user_id=user_id,
        lokasi_id=lokasi_id,
        nama=nama,
        alamat=alamat,
        jenis_ternak=jenis_ternak,
        jumlah_ternak=jumlah_ternak,
        jenis_pakan=jenis_pakan,
    )

    db.add(peternakan)
    db.commit()
    db.refresh(peternakan)

    return peternakan


def get_by_id(db: Session, peternakan_id: UUID) -> Peternakan | None:
    return (
        db.query(Peternakan)
        .options(joinedload(Peternakan.lokasi))
        .filter(
            Peternakan.id == peternakan_id,
            Peternakan.is_deleted.is_(False),
        )
        .first()
    )


def list_by_user(db: Session, user_id: UUID) -> list[Peternakan]:
    return (
        db.query(Peternakan)
        .options(joinedload(Peternakan.lokasi))
        .filter(
            Peternakan.user_id == user_id,
            Peternakan.is_deleted.is_(False),
        )
        .order_by(Peternakan.created_at.desc())
        .all()
    )


def update_peternakan(db: Session, peternakan: Peternakan, **kwargs) -> Peternakan:
    for key, value in kwargs.items():
        setattr(peternakan, key, value)

    db.commit()
    db.refresh(peternakan)

    return peternakan


def soft_delete_peternakan(db: Session, peternakan: Peternakan) -> Peternakan:
    peternakan.is_deleted = True

    db.commit()

    return peternakan
