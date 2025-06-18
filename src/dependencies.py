from .services.day_service import DayService
from .services.task_service import TaskService
import fastapi


def get_day_service(req: fastapi.Request) -> DayService:
    return req.app.state.day_service


def get_task_service(req: fastapi.Request) -> TaskService:
    return req.app.state.task_service
