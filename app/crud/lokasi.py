from sqlalchemy.orm import Session

from app.models.lokasi import Lokasi


def create_lokasi(
    db: Session,
    *,
    latitude: float,
    longitude: float,
    provinsi: str,
    kabupaten: str,
    kecamatan: str,
    desa: str,
    alamat_lengkap: str | None,
) -> Lokasi:
    lokasi = Lokasi(
        latitude=latitude,
        longitude=longitude,
        provinsi=provinsi,
        kabupaten=kabupaten,
        kecamatan=kecamatan,
        desa=desa,
        alamat_lengkap=alamat_lengkap,
    )

    db.add(lokasi)
    db.flush()  # supaya lokasi.id tersedia tanpa commit duluan

    return lokasi


def update_lokasi(db: Session, lokasi: Lokasi, **kwargs) -> Lokasi:
    for key, value in kwargs.items():
        setattr(lokasi, key, value)

    db.flush()

    return lokasi
