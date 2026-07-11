from datetime import date
from uuid import UUID

from sqlalchemy import Date
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Text

from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.enums import FermentationStatus
from app.models.mixins import UUIDMixin
from app.models.mixins import TimestampMixin

# Nama hari Bahasa Indonesia, dipakai [FermentationCycle.start_day_name] &
# [FermentationCycle.end_day_name] supaya semua client (app peternak, app
# pakar, dsb) nampilin nama hari yang konsisten tanpa masing-masing
# implementasi i18n sendiri-sendiri.
_HARI_ID = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]


class FermentationCycle(
    Base,
    UUIDMixin,
    TimestampMixin,
):
    """Satu siklus/sesi fermentasi yang berjalan di sebuah [Silo].

    Ini yang jadi sumber data "Hari ke-X dari Y" & progres fermentasi di
    Dashboard Peternak (sebelumnya dummy, lihat
    `DashboardDummyDataSource` di sisi app).

    Aturan bisnis: 1 silo cuma boleh punya 1 siklus berstatus RUNNING
    dalam satu waktu. Dijaga di 2 lapis: `FermentationService.start()`
    (pesan error yang enak dibaca) DAN partial unique index di database
    (lihat migration) supaya tetap aman walau ada race condition.
    """

    __tablename__ = "fermentation_cycles"

    silo_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("silos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    started_by: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    # Tanggal mulai fermentasi. Sengaja terpisah dari `created_at`
    # (kapan baris ini dibuat) karena user bisa input tanggal mundur,
    # mis. baru sempat catat di app padahal fermentasi sudah dimulai
    # kemarin.
    start_date: Mapped[date] = mapped_column(Date, nullable=False)

    planned_duration_days: Mapped[int] = mapped_column(Integer, nullable=False)

    # Dihitung & disimpan saat dibuat (start_date + planned_duration_days),
    # bukan cuma dihitung on-the-fly, supaya bisa langsung di-query/di-sort
    # (mis. "silo mana yang paling deket jatuh tempo") tanpa hitung ulang.
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Keisi kalau siklus ditutup manual (lihat FermentationService.finish),
    # baik selesai lebih cepat/telat maupun dibatalkan. NULL selama masih
    # RUNNING.
    actual_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    status: Mapped[FermentationStatus] = mapped_column(
        Enum(FermentationStatus, name="fermentation_status"),
        default=FermentationStatus.RUNNING,
        nullable=False,
    )

    catatan: Mapped[str | None] = mapped_column(Text, nullable=True)

    silo = relationship(
        "Silo",
        back_populates="fermentation_cycles",
    )

    starter = relationship(
        "User",
        foreign_keys=[started_by],
    )

    @property
    def current_day(self) -> int:
        """Hari ke berapa dari [planned_duration_days]. Kalau siklus
        sudah ditutup, dihitung sampai [actual_end_date] (bukan hari
        ini terus jalan), biar histori lama gak keliatan salah."""
        reference = self.actual_end_date or date.today()
        return max(1, (reference - self.start_date).days + 1)

    @property
    def is_overdue(self) -> bool:
        return self.status == FermentationStatus.RUNNING and date.today() > self.end_date

    @property
    def silo_nama(self) -> str:
        return self.silo.nama if self.silo else ""

    @property
    def peternakan_id(self) -> UUID | None:
        return self.silo.peternakan_id if self.silo else None

    @property
    def start_day_name(self) -> str:
        return _HARI_ID[self.start_date.weekday()]

    @property
    def end_day_name(self) -> str:
        return _HARI_ID[self.end_date.weekday()]
