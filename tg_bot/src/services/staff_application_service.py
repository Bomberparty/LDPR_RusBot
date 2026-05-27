import uuid
from datetime import datetime, date
from src.domain.entities.staff_application import StaffApplication
from src.domain.interfaces import IStaffApplicationRepository, IUnitOfWork
from src.services.interfaces import IStaffApplicationService

class StaffApplicationService(IStaffApplicationService):
    def __init__(self, repo: IStaffApplicationRepository, uow: IUnitOfWork):
        self.__repo = repo
        self.__uow = uow

    async def create_staff_application(
        self, staff_id: str, data: dict, pd_file_id: str | None = None, pd_agreement: bool = False
    ) -> StaffApplication:
        birth_date = data.get("birth_date")
        if isinstance(birth_date, str):
            try: birth_date = datetime.strptime(birth_date, "%d.%m.%Y").date()
            except ValueError: birth_date = date.today()
        elif not isinstance(birth_date, date):
            birth_date = date.today()

        obtained_at = data.get("obtained_data_at")
        if isinstance(obtained_at, str):
            try: obtained_at = datetime.strptime(obtained_at, "%d.%m.%Y %H:%M")
            except ValueError: 
                try: obtained_at = datetime.strptime(obtained_at, "%d.%m.%Y")
                except ValueError: obtained_at = datetime.now()
        elif not isinstance(obtained_at, datetime):
            obtained_at = datetime.now()

        app = StaffApplication(
            id=uuid.uuid4().hex,
            staff_id=str(staff_id),
            surname=data.get("surname", "-"),
            name=data.get("name", "-"),
            patronymic=data.get("patronymic"),
            region=data.get("region", "-"),
            city=data.get("city", "-"),
            home_address=data.get("home_address"),
            birth_date=birth_date,
            phone_number=data.get("phone_number", "-"),
            email=data.get("email", "-"),
            source="tg",
            obtained_data_at=obtained_at,
            application_text=data.get("application_text", "-"),
            personal_data_agreement=pd_agreement,
            application_file_id=data.get("file_id", "-"),
            personal_data_file_id=pd_file_id or "-"
        )
        async with self.__uow.atomic():
            return await self.__repo.create_staff_application(app)