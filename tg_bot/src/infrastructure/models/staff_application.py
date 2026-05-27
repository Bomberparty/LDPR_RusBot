import uuid
from datetime import datetime, date
from sqlalchemy import Text, DateTime, Date, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.entities.staff_application import StaffApplication
from src.infrastructure.database import Base

class StaffApplicationORM(Base):
    __tablename__ = "staff_applications"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    staff_id: Mapped[str] = mapped_column(String, nullable=False)
    surname: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    patronymic: Mapped[str | None] = mapped_column(Text, nullable=True)
    region: Mapped[str] = mapped_column(Text, nullable=False)
    city: Mapped[str] = mapped_column(Text, nullable=False)
    home_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    phone_number: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False, default="tg")
    obtained_data_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    application_text: Mapped[str] = mapped_column(Text, nullable=False)
    personal_data_agreement: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now())
    application_file_id: Mapped[str] = mapped_column(Text, nullable=False, default="-")
    personal_data_file_id: Mapped[str] = mapped_column(Text, nullable=False, default="-")

    async def to_domain(self) -> StaffApplication:
        return StaffApplication(
            id=self.id, staff_id=self.staff_id, surname=self.surname, name=self.name,
            patronymic=self.patronymic, region=self.region, city=self.city,
            home_address=self.home_address, birth_date=self.birth_date,
            phone_number=self.phone_number, email=self.email, source=self.source,
            obtained_data_at=self.obtained_data_at, application_text=self.application_text,
            personal_data_agreement=self.personal_data_agreement, created_at=self.created_at,
            application_file_id=self.application_file_id, personal_data_file_id=self.personal_data_file_id
        )

    @classmethod
    async def from_domain(cls, app: StaffApplication) -> 'StaffApplicationORM':
        return cls(
            id=app.id, staff_id=app.staff_id, surname=app.surname, name=app.name,
            patronymic=app.patronymic, region=app.region, city=app.city,
            home_address=app.home_address, birth_date=app.birth_date,
            phone_number=app.phone_number, email=app.email, source=app.source,
            obtained_data_at=app.obtained_data_at, application_text=app.application_text,
            personal_data_agreement=app.personal_data_agreement, created_at=app.created_at,
            application_file_id=app.application_file_id, personal_data_file_id=app.personal_data_file_id
        )