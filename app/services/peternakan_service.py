from uuid import UUID

from sqlalchemy.orm import Session

from app.crud import lokasi as lokasi_crud
from app.crud import peternakan as peternakan_crud
from app.models.peternakan import Peternakan
from app.models.user import User
from app.schemas.peternakan import PeternakanCreateRequest, PeternakanUpdateRequest
from app.services.geocoding_service import reverse_geocode


class PeternakanService:

    def __init__(self, db: Session):
        self.db = db

    def create(self, user: User, data: PeternakanCreateRequest) -> Peternakan:
        geo = reverse_geocode(data.latitude, data.longitude)

        lokasi = lokasi_crud.create_lokasi(
            self.db,
            latitude=data.latitude,
            longitude=data.longitude,
            provinsi=geo["provinsi"],
            kabupaten=geo["kabupaten"],
            kecamatan=geo["kecamatan"],
            desa=geo["desa"],
            alamat_lengkap=geo["alamat_lengkap"],
        )

        return peternakan_crud.create_peternakan(
            self.db,
            user_id=user.id,
            lokasi_id=lokasi.id,
            nama=data.nama,
            alamat=data.alamat,
            jenis_ternak=data.jenis_ternak,
            jumlah_ternak=data.jumlah_ternak,
            jenis_pakan=data.jenis_pakan,
        )

    def list_mine(self, user: User) -> list[Peternakan]:
        return peternakan_crud.list_by_user(self.db, user.id)

    def get_owned(self, user: User, peternakan_id: UUID) -> Peternakan:
        peternakan = peternakan_crud.get_by_id(self.db, peternakan_id)

        if peternakan is None:
            raise ValueError("Peternakan tidak ditemukan.")

        if peternakan.user_id != user.id and user.role.value != "admin":
            raise PermissionError("Anda tidak memiliki akses ke peternakan ini.")

        return peternakan

    def update(
        self,
        user: User,
        peternakan_id: UUID,
        data: PeternakanUpdateRequest,
    ) -> Peternakan:
        peternakan = self.get_owned(user, peternakan_id)

        updates = data.model_dump(exclude_unset=True, exclude_none=True)
        lat = updates.pop("latitude", None)
        lon = updates.pop("longitude", None)

        if lat is not None or lon is not None:
            new_lat = lat if lat is not None else peternakan.lokasi.latitude
            new_lon = lon if lon is not None else peternakan.lokasi.longitude

            geo = reverse_geocode(new_lat, new_lon)

            lokasi_crud.update_lokasi(
                self.db,
                peternakan.lokasi,
                latitude=new_lat,
                longitude=new_lon,
                **geo,
            )

        if updates:
            peternakan_crud.update_peternakan(self.db, peternakan, **updates)
        else:
            self.db.commit()
            self.db.refresh(peternakan)

        return peternakan

    def delete(self, user: User, peternakan_id: UUID) -> Peternakan:
        peternakan = self.get_owned(user, peternakan_id)
        return peternakan_crud.soft_delete_peternakan(self.db, peternakan)
