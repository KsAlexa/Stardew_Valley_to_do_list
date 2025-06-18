from fastapi import APIRouter, Depends
from .handlers_models import *
from ..dependencies import get_day_service, get_task_service
from ..services.day_service import DayService
from ..services.task_service import TaskService

router = APIRouter(
    prefix="/day",
    tags=["day"],
    responses={404: {'description': 'Entity not found'}}
)


def _get_current_day_details(day_service: DayService, task_service: TaskService) -> DayResponse:
    current_day = day_service.get_active()
    day_tasks = task_service.get_all_by_day_id(current_day.id)
    return DayResponse.from_day(current_day, day_tasks)


@router.get("/current", status_code=200)
def get_current_day_info_handle(
        day_service: DayService = Depends(get_day_service),
        task_service: TaskService = Depends(get_task_service)
) -> DayResponse:
    return _get_current_day_details(day_service, task_service)


@router.put("/current", status_code=200)
def set_current_day_handle(
        request: SetCurrentDayRequest,
        day_service: DayService = Depends(get_day_service),
        task_service: TaskService = Depends(get_task_service)
) -> DayResponse:
    day_service.set_current_day(request.year, request.season, request.number)
    return _get_current_day_details(day_service, task_service)


# надо при перелистывании дня оставлять tasks type == daily, а tasks type == one-time помечать завершенными make_task_completed()
@router.post("/next", status_code=200)
def set_next_day_handle(
        day_service: DayService = Depends(get_day_service),
        task_service: TaskService = Depends(get_task_service)
) -> DayResponse:
    day_service.set_next_day()
    return _get_current_day_details(day_service, task_service)
