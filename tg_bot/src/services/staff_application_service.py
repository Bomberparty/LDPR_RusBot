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

        # ✅ Гарантия: ни одно строковое поле не будет None или ""
        def _safe(val: str | None) -> str:
            return val if val else "-"

        app = StaffApplication(
            id=uuid.uuid4().hex,
            staff_id=str(staff_id),
            surname=_safe(data.get("surname")),
            name=_safe(data.get("name")),
            patronymic=_safe(data.get("patronymic")),
            region=_safe(data.get("region")),
            city=_safe(data.get("city")),
            home_address=_safe(data.get("home_address")),
            birth_date=birth_date,
            phone_number=_safe(data.get("phone_number")),
            email=_safe(data.get("email")),
            source="tg",
            obtained_data_at=obtained_at,
            application_text=_safe(data.get("application_text")),
            personal_data_agreement=pd_agreement,
            application_file_id=_safe(data.get("file_id")),
            personal_data_file_id=_safe(pd_file_id)
        )
        async with self.__uow.atomic():
            return await self.__repo.create_staff_application(app)