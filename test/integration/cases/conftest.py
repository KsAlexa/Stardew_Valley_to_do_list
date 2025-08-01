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


@pytest.fixture
def default_active_day():
    return {
        'id': 1,
        'year': 1,
        'season': 'spring', 
        'number': 1,
        'active': True
    }

@pytest.fixture
def default_day_state(client, default_active_day):
    response = client.get('/day/current')
    assert response.status_code == 200
    
    state = response.json()
    
    current_day_info = state['current_day_info']
    assert current_day_info['id'] == default_active_day['id']
    assert current_day_info['year'] == default_active_day['year']
    assert current_day_info['season'] == default_active_day['season']
    assert current_day_info['number'] == default_active_day['number']
    assert current_day_info['active'] == default_active_day['active']

    assert len(current_day_info['tasks']) == 0
    assert len(state['all_completed_tasks']) == 0
    
    return state