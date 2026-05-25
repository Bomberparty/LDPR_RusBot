from src.core.di import DeclarativeContainer, providers
from src.domain.entities import Sources
from src.domain.interfaces import IUnitOfWork, IUserRepository, IStringSorterRepository, IApplicationRepository
from src.infrastructure.repositories import ApplicationRepository
from src.services import ApplicationService
from src.services.interfaces import IApplicationService
from src.infrastructure import Database, UnitOfWork
from src.infrastructure.interfaces import IDatabase
from src.infrastructure.repositories import UserRepository, LevenshteinRepository, FuzzywuzzyRepository
from src.services import UserService
from src.services.interfaces import IUserService
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
        ApplicationService, app_repo=application_repository, user_repo=user_repository, uow=uow, source=Sources.TG
    )
