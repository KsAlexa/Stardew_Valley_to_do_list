from http.client import HTTPException

from fastapi import APIRouter, HTTPException
from .models import *
from .. import repository, config, services

router = APIRouter(
    prefix="/day",
    tags=["day"]
)

day_repository = repository.DayRepository(config.DB_PATH)
task_repository = repository.TaskRepository(config.DB_PATH)
day_service = services.DayService(day_repository, task_repository)
task_service = services.TaskService(task_repository, day_repository)


def _get_current_day_details() -> DayResponse:
    current_day = day_service.get_active()
    if current_day is None:
        raise HTTPException(status_code=400, detail='No active day. Set a day first')
    day_tasks = task_service.get_all_by_day_id(current_day.id)
    current_day_details = DayResponse(
        id=current_day.id,
        year=current_day.year,
        season=current_day.season,
        number=current_day.number,
        active=True,
        tasks=day_tasks
    )
    return current_day_details


@router.get("/current", status_code=200,
            responses={400: {'description': 'No active day. Set a day first'}}
            )
def get_current_day_info_handle() -> DayResponse:
    return _get_current_day_details()


@router.put("/current", status_code=200)
def set_current_day_handle(request: SetCurrentDayRequest) -> DayResponse:
    day_service.set_current_day(request.year, request.season, request.number)
    return _get_current_day_details()



# надо при перелистывании дня оставлять tasks type == daily, а tasks type == one-time помечать завершенными make_task_completed()
@router.post("/next", status_code=200,
             responses={404: {'description': 'No active day set. Cannot set the next day'}}
             )
def set_next_day_handle() -> DayResponse:
    day_service.set_next_day()
    return _get_current_day_details()
