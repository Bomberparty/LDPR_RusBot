from abc import ABC, abstractmethod
from contextlib import _AsyncGeneratorContextManager

from .entities import User, Sources, Application, Role
from .entities.staff_application import StaffApplication

class IUnitOfWork(ABC):
    @abstractmethod
    def atomic(self) -> _AsyncGeneratorContextManager[None, None]:
        ...


class IUserRepository(ABC):
    @abstractmethod
    async def create_user(self, user: User) -> User:
        ...

    @abstractmethod
    async def get_user(self, user_id: int, source: Sources) -> User:
        ...

    @abstractmethod
    async def is_phone_number_existing(self, phone_number: str) -> bool:
        ...
    
    @abstractmethod
    async def is_email_existing(self, email: str) -> bool:
        ...

    @abstractmethod
    async def get_users(
        self, 
        skip: int = 0, 
        limit: int = 100,
        **filters
    ) -> list[User]:
        ...

    @abstractmethod
    async def update_user_news_subscription(
            self, user_id: int, source: Sources, news_subscription: bool
    ) -> User:
        ...
    
    @abstractmethod
    async def update_user_role(self, user_id: int, source: Sources, role: Role) -> User:
        ...


class IStringSorterRepository(ABC):
    @abstractmethod
    async def sort_by_similarity(self, target: str, string_list: list[str]) -> list[str]:
        ...
        
class IApplicationRepository(ABC):
    @abstractmethod
    async def create_application(self, app: Application) -> Application:
        ...
    @abstractmethod
    async def get_user_applications(self, user_id: int, skip: int = 0, limit: int = 4) -> list[Application]:
        ...
    @abstractmethod
    async def get_user_applications_count(self, user_id: int) -> int:
        ...

class IGeminiExtractor(ABC):
    @abstractmethod
    async def extract_application_data(self, image_bytes: bytes) -> dict[str, str]:
        ...
    
    @abstractmethod
    async def extract_staff_application_data(self, image_bytes: bytes) -> dict:
        ...


class IStaffApplicationRepository(ABC):
    @abstractmethod
    async def create_staff_application(self, app: StaffApplication) -> StaffApplication:
        ...