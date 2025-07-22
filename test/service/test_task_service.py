import pytest
from unittest.mock import MagicMock, call
from src import errors
from src.services.task_service import TaskService
from src.services.task_service import DayService
from src.entities.task_entities import Task
from src.entities.day_entities import Day
from src.migration import create_database_and_tables
from pathlib import Path
from src.repository import day_repository, task_repository


def _compare_task_objects_without_id(task1: Task, task2: Task):
    assert task1.name == task2.name, 'Names do not match'
    assert task1.day_id == task2.day_id, 'Day_ids do not match'
    assert task1.type == task2.type, 'Types do not match'
    assert task1.status == task2.status, 'Status do not match'


@pytest.fixture
def mock_task_repo():
    return MagicMock()

@pytest.fixture
def mock_day_service():
    return MagicMock()

@pytest.fixture
def task_service(mock_task_repo, mock_day_service):
    return TaskService(mock_task_repo, mock_day_service)

@pytest.fixture
def active_day():
    return Day(year=1, season='spring', number=1, active=True, day_id=1)


@pytest.fixture
def get_test_db_path(tmp_path: Path) -> str:
    test_db_path = tmp_path / "test_day_db.sqlite"
    create_database_and_tables(str(test_db_path))
    return str(test_db_path)

@pytest.fixture
def task_repo(get_test_db_path: str) -> task_repository.TaskRepository:
    return task_repository.TaskRepository(get_test_db_path)

@pytest.fixture
def task_service_with_tasks_in_db(task_repo: task_repository.TaskRepository,
                                  mock_day_service: MagicMock) -> TaskService:
    tasks = [
        Task(name='Daily task', day_id=1, type='daily', status='active', task_id=1),
        Task(name='One-time active task', day_id=1, type='one-time', status='active', task_id=2),
        Task(name='One-time completed task', day_id=1, type='one-time', status='completed', task_id=3)
    ]
    for task in tasks:
        task_repo.insert(task)
    return TaskService(task_repo, mock_day_service)


def test_create_task_success(task_service, mock_task_repo, mock_day_service, active_day):
    current_active_day = mock_day_service.get_active.return_value = active_day

    new_task_id = 1
    task_name = 'test task'
    expected_task = Task(name=task_name, day_id=current_active_day.id, type='one-time', status='active',
                                 task_id=new_task_id)

    mock_task_repo.insert.return_value = expected_task

    created_task = task_service.create_task(task_name)

    mock_day_service.get_active.assert_called_once()
    mock_task_repo.insert.assert_called_once()

    assert created_task == expected_task


def test_create_existent_task_fails(task_service_with_tasks_in_db, mock_day_service, active_day):
    mock_day_service.get_active.return_value = active_day

    existent_task_name = 'One-time active task'

    with pytest.raises(errors.DuplicateTaskNameException) as exc_info:
        task_service_with_tasks_in_db.create_task(existent_task_name)

    assert "already exists" in str(exc_info.value)
