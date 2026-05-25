from datetime import datetime, UTC
from sqlalchemy import String, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.entities.application import Application
from src.infrastructure.database import Base


class ApplicationORM(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    sender_fio: Mapped[str | None] = mapped_column(String, nullable=True)
    deputy_fio: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    text: Mapped["ApplicationTextORM"] = relationship(back_populates="application", uselist=False, lazy="joined")

    async def to_domain(self) -> Application:
        return Application(
            id=self.id,
            user_id=self.user_id,
            sender_fio=self.sender_fio,
            deputy_fio=self.deputy_fio,
            application_text=self.text.application_text if self.text else "",
            created_at=self.created_at
        )


class ApplicationTextORM(Base):
    __tablename__ = "application_texts"

    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"), primary_key=True)
    application_text: Mapped[str] = mapped_column(Text, nullable=False)
    
    application: Mapped["ApplicationORM"] = relationship(back_populates="text")
