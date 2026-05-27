from src.domain.entities.application import Application
from src.domain.interfaces import IApplicationRepository
from src.services.interfaces import IApplicationService
from src.domain.interfaces import IUnitOfWork

class ApplicationService(IApplicationService):
    def __init__(self, app_repo: IApplicationRepository, uow: IUnitOfWork):
        self.__app_repo = app_repo
        self.__uow = uow

    async def create_application(self, user_id: int, text: str) -> Application:
        # ✅ Финальная проверка текста перед сохранением
        text = text or "-"
        app = Application(id=0, user_id=user_id, application_text=text)
        async with self.__uow.atomic():
            return await self.__app_repo.create_application(app)

    async def get_user_applications(self, user_id: int, page: int = 0) -> tuple[list[Application], int]:
        async with self.__uow.atomic():
            count = await self.__app_repo.get_user_applications_count(user_id)
            apps = await self.__app_repo.get_user_applications(user_id, skip=page * 4, limit=4)
            return apps, count

    async def get_applications_count(self, user_id: int) -> int:
        async with self.__uow.atomic():
            return await self.__app_repo.get_user_applications_count(user_id)