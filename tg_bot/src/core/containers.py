from src.core.di import DeclarativeContainer, providers
from src.domain.entities import Sources
from src.domain.interfaces import IUnitOfWork, IUserRepository, IStringSorterRepository, IApplicationRepository, IStaffApplicationRepository
from src.infrastructure.repositories import ApplicationRepository
from src.services import ApplicationService, StaffApplicationService
from src.services.interfaces import IApplicationService, IStaffApplicationService
from src.infrastructure import Database, UnitOfWork
from src.infrastructure.interfaces import IDatabase
from src.infrastructure.repositories import UserRepository, LevenshteinRepository, FuzzywuzzyRepository, StaffApplicationRepository
from src.services import UserService
from src.services.interfaces import IUserService
from src.domain.interfaces import IGeminiExtractor
from src.infrastructure.gemini import GeminiExtractor
from src.domain.entities import Sources
from src.core import config


class Container(DeclarativeContainer):
    database: providers.Singleton[IDatabase] = providers.Singleton(
        Database, "db.sqlite3"
    )
    uow: providers.Singleton[IUnitOfWork] = providers.Singleton(
        UnitOfWork, database=database
    )
    user_repository: providers.Factory[IUserRepository] = providers.Factory(
        UserRepository, uow=uow
    )
    string_sorter: providers.Factory[IStringSorterRepository] = providers.Factory(
        FuzzywuzzyRepository
    )
    user_service: providers.Factory[IUserService] = providers.Factory(
        UserService, user_repo=user_repository, uow=uow, string_sorter_repo=string_sorter, source=Sources.TG
    )
    log_chat: providers.Object[str] = providers.Object(config.log_chat)
    admin_ids: providers.Object[list[int]] = providers.Object(config.admin_ids)
    application_repository: providers.Factory[IApplicationRepository] = providers.Factory(
        ApplicationRepository, uow=uow
    )
    app_service: providers.Factory[IApplicationService] = providers.Factory(
        ApplicationService, app_repo=application_repository, uow=uow
    )
    staff_application_repository: providers.Factory[IStaffApplicationRepository] = providers.Factory(
        StaffApplicationRepository, uow=uow
    )
    staff_app_service: providers.Factory[IStaffApplicationService] = providers.Factory(
        StaffApplicationService, repo=staff_application_repository, uow=uow
    )
    gemini_extractor: providers.Factory[IGeminiExtractor] = providers.Factory(
        GeminiExtractor,
        api_key=config.GEMINI_API_KEY,
        proxy_url_for_sdk=config.PROXY_URL_FOR_SDK
    )