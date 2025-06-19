from .services.day_service import DayService
from .services.task_service import TaskService
import fastapi

# Функции-'поставщики' (провайдеры). FastAPI автоматически передаст в них объект текущего запроса `req`.
# Получают доступ к состоянию приложения (req.app.state) и возвращают из него нужный сервис, который был создан при старте в main
def get_day_service(req: fastapi.Request) -> DayService:
# Через запрос `req` получаем доступ к главному объекту `app`,
# затем к его состоянию `state` и оттуда возвращаем единственный экземпляр `day_service`, созданный в lifespan.
    return req.app.state.day_service


def get_task_service(req: fastapi.Request) -> TaskService:
    return req.app.state.task_service
