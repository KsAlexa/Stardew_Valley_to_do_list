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
from src.api.handlers_models import *
from typing import Callable, List
from helpers import assert_task_data, assert_day_data
from service_client import ServiceClient

@pytest.fixture
def test_db_path(tmp_path: Path) -> str:
    test_db_path = tmp_path / "integration_test.sqlite"
    create_database_and_tables(str(test_db_path))
    return str(test_db_path)


@pytest.fixture
def test_client(test_db_path: str):
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
def service_client(test_client: TestClient) -> ServiceClient:
    return ServiceClient(test_client)

@pytest.fixture
def default_active_day() -> CurrentDayResponse:
    return CurrentDayResponse(
        id=1,
        year=1,
        season=DaySeason.spring,
        number=1,
        active=True,
        tasks=[]
    )

@pytest.fixture
def default_day_state(service_client, default_active_day) -> CurrentStateResponse:
    state = service_client.get_current_state()
    
    current_day_info = state.current_day_info

    assert_day_data(
        current_day_info,
        expected_id=default_active_day.id,
        expected_year=default_active_day.year,
        expected_season=default_active_day.season,
        expected_number=default_active_day.number,
        expected_active=default_active_day.active,
        expected_tasks=[]
    )

    assert len(state.all_completed_tasks) == 0
    
    return state

@pytest.fixture
def task_factory(service_client, default_day_state: CurrentStateResponse) -> Callable[[int], List[TaskResponse]]:
    def _task_factory(tasks_count: int) -> List[TaskResponse]:
        if tasks_count <= 0:
            return []
            
        created_tasks_list = []
        current_day_id = default_day_state.current_day_info.id
        
        for task_index in range(1, tasks_count + 1):
            task_name = f'Тестовая задача {task_index}'
            request = TaskNameRequest(name=task_name)
            created_task_obj = service_client.create_task(request)
            
            assert_task_data(
                created_task_obj, 
                expected_name=task_name, 
                expected_status=TaskStatus.active,
                expected_type=TaskType.one_time,
                expected_day_id=current_day_id
            )
            created_tasks_list.append(created_task_obj)
            
        created_tasks_list.sort(key=lambda task: task.id)
        return created_tasks_list

    return _task_factory


@pytest.fixture
def day_with_three_tasks_factory(service_client) -> Callable[[SetCurrentDayRequest], tuple[CurrentStateResponse, TaskResponse, TaskResponse, TaskResponse]]:
    def _day_factory(
        request: SetCurrentDayRequest,
        *,
        active_one_time_name: str = 'Однодневная активная',
        completed_one_time_name: str = 'Однодневная завершенная',
        daily_name: str = 'Ежедневная задача',
    ) -> tuple[CurrentStateResponse, TaskResponse, TaskResponse, TaskResponse]:

        state_after_set = service_client.set_current_day(request)
        current_day_id = state_after_set.current_day_info.id

        assert_day_data(
            state_after_set.current_day_info,
            expected_year=request.year,
            expected_season=request.season,
            expected_number=request.number,
            expected_active=True,
            expected_tasks=[],
        )

        active_one_time_task = service_client.create_task(TaskNameRequest(name=active_one_time_name))
        assert_task_data(
            active_one_time_task,
            expected_name=active_one_time_name,
            expected_type=TaskType.one_time,
            expected_status=TaskStatus.active,
            expected_day_id=current_day_id,
        )

        new_task = service_client.create_task(TaskNameRequest(name=completed_one_time_name))
        completed_one_time_task = service_client.complete_task(new_task.id)
        assert_task_data(
            completed_one_time_task,
            expected_name=completed_one_time_name,
            expected_type=TaskType.one_time,
            expected_status=TaskStatus.completed,
            expected_day_id=current_day_id,
        )

        new_task = service_client.create_task(TaskNameRequest(name=daily_name))
        daily_task = service_client.make_task_daily(new_task.id)
        assert_task_data(
            daily_task,
            expected_name=daily_name,
            expected_type=TaskType.daily,
            expected_status=TaskStatus.active,
            expected_day_id=current_day_id,
        )

        state_with_tasks = service_client.get_current_state()
        assert_day_data(
            state_with_tasks.current_day_info,
            expected_year=request.year,
            expected_season=request.season,
            expected_number=request.number,
            expected_active=True,
            expected_tasks=[active_one_time_task, daily_task],
        )
        assert len(state_with_tasks.all_completed_tasks) == 1

        return state_with_tasks, active_one_time_task, completed_one_time_task, daily_task

    return _day_factory