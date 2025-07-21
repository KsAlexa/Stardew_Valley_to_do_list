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

# С помощью Depends(get_day_service) передается заранее созданный объект сервиса - экземпляр DayService из app.state
# При app.dependency_overrides Depends(get_day_service) вместо вызова функции get_day_service() вызовет get_mock_day_service()

def _get_current_day_details(day_service: DayService, task_service: TaskService) -> CurrentStateResponse:
    current_day = day_service.get_active()
    day_tasks = task_service.get_all_by_day_id(current_day.id)
    active_day_tasks = [task for task in day_tasks if task.status == 'active']
    completed_tasks = task_service.get_all_completed()
    return CurrentStateResponse.from_entities(current_day, active_day_tasks, completed_tasks)


@router.get("/current", response_model=CurrentStateResponse, status_code=200)
def get_current_day_info_handle(
        day_service: DayService = Depends(get_day_service),
        task_service: TaskService = Depends(get_task_service)
) -> CurrentStateResponse:
    return _get_current_day_details(day_service, task_service)


@router.put("/current", response_model=CurrentStateResponse, status_code=200)
def set_current_day_handle(
        request: SetCurrentDayRequest,
        day_service: DayService = Depends(get_day_service),
        task_service: TaskService = Depends(get_task_service)
) -> CurrentStateResponse:
    day_service.set_current_day(request.year, request.season, request.number)
    return _get_current_day_details(day_service, task_service)


# надо при перелистывании дня оставлять tasks type == daily, а tasks type == one-time помечать завершенными make_task_completed()
@router.post("/next", response_model=CurrentStateResponse, status_code=200)
def set_next_day_handle(
        day_service: DayService = Depends(get_day_service),
        task_service: TaskService = Depends(get_task_service)
) -> CurrentStateResponse:
    day_service.set_next_day()
    return _get_current_day_details(day_service, task_service)
