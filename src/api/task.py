from fastapi import APIRouter
from .models import *
from .. import repository, config, services, errors

router = APIRouter(
    prefix="/task",
    tags=["task"],
    responses={404: {'description': 'Entity not found'},
               400: {'description': 'Invalid state'}
               }
)

day_repository = repository.DayRepository(config.DB_PATH)
task_repository = repository.TaskRepository(config.DB_PATH)
day_service = services.DayService(day_repository, task_repository)
task_service = services.TaskService(task_repository, day_repository)


@router.post("/", status_code=200)
def create_task_handle(request: AddTaskRequest) -> TaskResponse:
    new_task = task_service.create_task(request.name)
    return TaskResponse.from_task(new_task)


@router.patch("/{id}/complete", status_code=200)
def make_task_complete_handle(id: int) -> TaskResponse:
    updated_task = task_service.make_task_complete(id)
    return TaskResponse.from_task(updated_task)


@router.patch("/{id}/active", status_code=200)
def make_task_active_handle(id: int) -> TaskResponse:
    updated_task = task_service.make_task_active(id)
    return TaskResponse.from_task(updated_task)


@router.patch("/{id}/daily", status_code=200)
def make_task_daily_handle(id: int) -> TaskResponse:
    updated_task = task_service.make_task_daily(id)
    return TaskResponse.from_task(updated_task)


@router.patch("/{id}/one_time", status_code=200)
def make_task_one_time_handle(id: int) -> TaskResponse:
    updated_task = task_service.make_task_one_time(id)
    return TaskResponse.from_task(updated_task)
