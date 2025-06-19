from fastapi import FastAPI
from contextlib import asynccontextmanager

from starlette.datastructures import State

from . import migration, config
from .api import *
from .repository import DayRepository, TaskRepository
from .services import DayService, TaskService

# Определение "состояния" приложения ('чертеж')
# Объект для хранения общих ресурсов, доступных во всем приложении
class ApplicationState(State):
    day_service: DayService
    task_service: TaskService

# Свой класс приложения по заданному 'чертежу'
class Application(FastAPI):
    state: ApplicationState

# Выполняется один раз при запуске приложения
# Код после `yield` выполняется один раз при остановке приложения.
@asynccontextmanager
async def lifespan(application: Application):
    print("Starting lifespan")
    print("Building dependencies")

    task_repository = TaskRepository(config.DB_PATH)
    day_repository = DayRepository(config.DB_PATH)
    day_service = DayService(day_repository, task_repository)
    task_service = TaskService(task_repository, day_service)

# Сохранение созданных сервисов в состояние приложения 'application.state'
# Теперь они доступны из любой части приложения
    application.state.day_service = day_service
    application.state.task_service = task_service
    print("Dependencies built")
    migration.create_database_and_tables(config.DB_PATH)
# `yield` передает управление приложению. Оно начинает работать и принимать запросы.
    yield
    print("Exiting lifespan")

# Создание экземпляра приложения и передача ему менеджера жизненного цикла
app = Application(lifespan=lifespan)
# Регистрация роутов
app.include_router(day_handlers.router)
app.include_router(task_handlers.router)
