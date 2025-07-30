import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from src.main import app
from src.dependencies import get_task_service, get_day_service
from src.services.task_service import TaskService
from src.services.day_service import DayService
from src.repository.task_repository import TaskRepository
from src.repository.day_repository import DayRepository
from src.migration import create_database_and_tables


@pytest.fixture
def test_db_path(tmp_path: Path) -> str:
    test_db_path = tmp_path / "integration_test.sqlite"
    create_database_and_tables(str(test_db_path))
    return str(test_db_path)


@pytest.fixture
def client(test_db_path: str):
    task_repo = TaskRepository(test_db_path)
    day_repo = DayRepository(test_db_path)

    day_service = DayService(day_repo, task_repo)
    task_service = TaskService(task_repo, day_service)

    app.dependency_overrides[get_day_service] = lambda: day_service
    app.dependency_overrides[get_task_service] = lambda: task_service

    client = TestClient(app)
    
    yield client

    app.dependency_overrides.clear()


    # 1. Получить дефолтный день ОР: year=1, season = 'spring', day = 1
    # 2. Создать 3 задачи ОР: задачи созданы такие
    # 3. Переименовать 1 задачу ОР: переименована
    # 4. Поменять тип 2 задачи ОР: поменян тип
    # 5. Завершить 3 задачу ОР: завершена
    # 6. Перейти на следующий день ОР: daily задача осталась, а one-day стала completed (но должна остаться в общем списке, итого в списке 2 задачи завершенные)

