from fastapi import APIRouter, Depends
from .handlers_models import *
from ..services.task_service import TaskService
from ..dependencies import get_task_service

router = APIRouter(
    prefix="/task",
    tags=["task"],
    responses={404: {'description': 'Entity not found'},
               400: {'description': 'Invalid state'}
               }
)


@router.post("/", status_code=200)
def create_task_handle(
        request: TaskNameRequest,
        task_service: TaskService = Depends(get_task_service)
) -> TaskResponse:
    new_task = task_service.create_task(request.name)
    return TaskResponse.from_task(new_task)


@router.patch("/{id}/complete", status_code=200)
def make_task_complete_handle(
        id: int,
        task_service: TaskService = Depends(get_task_service)
) -> TaskResponse:
    updated_task = task_service.make_completed(id)
    return TaskResponse.from_task(updated_task)


@router.patch("/{id}/active", status_code=200)
def make_task_active_handle(
        id: int,
        task_service: TaskService = Depends(get_task_service)
) -> TaskResponse:
    updated_task = task_service.make_active(id)
    return TaskResponse.from_task(updated_task)


@router.patch("/{id}/daily", status_code=200)
def make_task_daily_handle(
        id: int,
        task_service: TaskService = Depends(get_task_service)
) -> TaskResponse:
    updated_task = task_service.make_daily(id)
    return TaskResponse.from_task(updated_task)


@router.patch("/{id}/one_time", status_code=200)
def make_task_one_time_handle(
        id: int,
        task_service: TaskService = Depends(get_task_service)
) -> TaskResponse:
    updated_task = task_service.make_one_time(id)
    return TaskResponse.from_task(updated_task)


@router.patch("/{id}/rename", status_code=200)
def edit_task_name_handle(
        id: int,
        request: TaskNameRequest,
        task_service: TaskService = Depends(get_task_service)
) -> TaskResponse:
    updated_task = task_service.edit_name(id, request.name)
    return TaskResponse.from_task(updated_task)
