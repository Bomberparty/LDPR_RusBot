from src.domain.entities.staff_application import StaffApplication
from src.domain.interfaces import IStaffApplicationRepository
from src.infrastructure.interfaces import IDatabaseUnitOfWork
from src.infrastructure.models.staff_application import StaffApplicationORM

class StaffApplicationRepository(IStaffApplicationRepository):
    def __init__(self, uow: IDatabaseUnitOfWork):
        self.__uow = uow

    async def create_staff_application(self, app: StaffApplication) -> StaffApplication:
        session = self.__uow.get_session()
        app_orm = await StaffApplicationORM.from_domain(app)
        session.add(app_orm)
        await session.commit()
        await session.refresh(app_orm)
        return await app_orm.to_domain()