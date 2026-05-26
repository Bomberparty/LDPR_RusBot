from datetime import datetime, UTC
from sqlalchemy import Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.entities.application import Application
from src.infrastructure.database import Base

class ApplicationORM(Base):
    __tablename__ = "application_texts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    application_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    async def to_domain(self) -> Application:
        return Application(
            id=self.id,
            user_id=self.user_id,
            application_text=self.application_text,
            created_at=self.created_at
        )