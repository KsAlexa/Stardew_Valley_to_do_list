from fastapi import FastAPI
from contextlib import asynccontextmanager

from starlette.datastructures import State

from . import migration, config
from .api import *
from .repository import DayRepository, TaskRepository
from .services import DayService, TaskService


class ApplicationState(State):
    day_service: DayService
    task_service: TaskService


class Application(FastAPI):
    state: ApplicationState


@asynccontextmanager
async def lifespan(application: Application):
    print("Starting lifespan")
    print("Building dependencies")

    task_repository = TaskRepository(config.DB_PATH)
    day_repository = DayRepository(config.DB_PATH)
    day_service = DayService(day_repository, task_repository)
    task_service = TaskService(task_repository, day_service)

    application.state.day_service = day_service
    application.state.task_service = task_service
    print("Dependencies built")
    migration.create_database_and_tables(config.DB_PATH)
    yield
    print("Exiting lifespan")


app = Application(lifespan=lifespan)

app.include_router(day_handlers.router)
app.include_router(task_handlers.router)
