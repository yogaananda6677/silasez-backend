from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.enums import FermentationStatus, UserRole
from app.crud import fermentation_cycle as cycle_crud
from app.crud import silo as silo_crud
from app.crud.chat_room import chat_room as chat_room_crud
from app.models.fermentation_cycle import FermentationCycle
from app.models.silo import Silo
from app.models.user import User
from app.schemas.fermentation import CompleteFermentationRequest, StartFermentationRequest


class FermentationService:

    def __init__(self, db: Session):
        self.db = db

    def _get_silo_or_404(self, silo_id: UUID) -> Silo:
        silo = silo_crud.get_by_id(self.db, silo_id)

        if silo is None:
            raise ValueError("Silo tidak ditemukan.")

        return silo

    def _assert_can_write(self, user: User, silo: Silo) -> None:
        if user.role == UserRole.ADMIN:
            return
        if silo.peternakan.user_id != user.id:
            raise PermissionError("Anda tidak memiliki akses ke silo ini.")

    def _assert_can_read(self, user: User, silo: Silo) -> None:
        if user.role == UserRole.ADMIN or silo.peternakan.user_id == user.id:
            return

        if user.role == UserRole.PAKAR and chat_room_crud.has_consulted(
            self.db,
            pakar_id=user.id,
            peternak_id=silo.peternakan.user_id,
        ):
            return

        raise PermissionError("Anda tidak memiliki akses ke data silo ini.")

    def start(
        self,
        user: User,
        silo_id: UUID,
        data: StartFermentationRequest,
    ) -> FermentationCycle:
        silo = self._get_silo_or_404(silo_id)
        self._assert_can_write(user, silo)

        if cycle_crud.get_active_by_silo(self.db, silo_id) is not None:
            raise ValueError(
                "Silo ini masih punya siklus fermentasi yang berjalan. "
                "Selesaikan dulu siklus itu sebelum memulai yang baru."
            )

        return cycle_crud.create(
            self.db,
            silo_id=silo_id,
            started_by=user.id,
            start_date=data.start_date or date.today(),
            planned_duration_days=21,
            catatan=data.catatan,
        )

    def get_active(self, user: User, silo_id: UUID) -> FermentationCycle | None:
        silo = self._get_silo_or_404(silo_id)
        self._assert_can_read(user, silo)

        return cycle_crud.get_active_by_silo(self.db, silo_id)

    def list_history(self, user: User, silo_id: UUID) -> list[FermentationCycle]:
        silo = self._get_silo_or_404(silo_id)
        self._assert_can_read(user, silo)

        return cycle_crud.list_by_silo(self.db, silo_id)

    def finish(
        self,
        user: User,
        cycle_id: UUID,
        data: CompleteFermentationRequest,
    ) -> FermentationCycle:
        cycle = cycle_crud.get_by_id(self.db, cycle_id)

        if cycle is None:
            raise ValueError("Siklus fermentasi tidak ditemukan.")

        self._assert_can_write(user, cycle.silo)

        if cycle.status != FermentationStatus.RUNNING:
            raise ValueError("Siklus fermentasi ini sudah tidak berjalan.")

        if data.status not in (FermentationStatus.COMPLETED, FermentationStatus.CANCELLED):
            raise ValueError("Status akhir harus SELESAI atau DIBATALKAN.")

        return cycle_crud.finish(
            self.db,
            cycle,
            status=data.status,
            catatan=data.catatan,
        )
