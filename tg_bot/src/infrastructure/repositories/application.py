from sqlalchemy import select, func
from src.domain.entities.application import Application
from src.domain.interfaces import IApplicationRepository
from src.infrastructure.interfaces import IDatabaseUnitOfWork
from src.infrastructure.models.application import ApplicationORM

class ApplicationRepository(IApplicationRepository):
    def __init__(self, uow: IDatabaseUnitOfWork):
        self.__uow = uow

    async def create_application(self, app: Application) -> Application:
        session = self.__uow.get_session()
        app_orm = ApplicationORM(
            user_id=app.user_id,
            application_text=app.application_text
        )
        session.add(app_orm)
        await session.commit()
        await session.refresh(app_orm)
        return await app_orm.to_domain()

    async def get_user_applications(self, user_id: int, skip: int = 0, limit: int = 4) -> list[Application]:
        session = self.__uow.get_session()
        stmt = (
            select(ApplicationORM)
            .where(ApplicationORM.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(ApplicationORM.created_at.desc())
        )
        result = await session.execute(stmt)
        apps = result.scalars().all()
        return [await a.to_domain() for a in apps]

    async def get_user_applications_count(self, user_id: int) -> int:
        session = self.__uow.get_session()
        stmt = select(func.count()).select_from(ApplicationORM).where(ApplicationORM.user_id == user_id)
        return await session.scalar(stmt) or 0