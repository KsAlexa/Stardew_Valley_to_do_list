import pytest
from unittest.mock import MagicMock, call
from src import errors
from src.services.task_service import TaskService
from src.entities.task_entities import Task
from src.entities.day_entities import Day

def _compare_task_objects_without_id(task1: Task, task2: Task):
    assert task1.name == task2.name, 'Names do not match'
    assert task1.day_id == task2.day_id, 'Day_ids do not match'
    assert task1.type == task2.type, 'Types do not match'
    assert task1.status == task2.status, 'Status do not match'


@pytest.fixture
def mock_task_repo():
    return MagicMock()

@pytest.fixture
def mock_day_repo():
    return MagicMock()

@pytest.fixture
def task_service(mock_task_repo, mock_day_repo):
    return TaskService(mock_task_repo, mock_day_repo)


def test_create_task_success(task_service, mock_task_repo, mock_day_repo):
    current_active_day = Day(year=1, season='winter', number=15, active=True, day_id=2)
    mock_day_repo.get_active.return_value = current_active_day

    new_task_id = 1
    task_name = 'test task'
    expected_task = Task(name = task_name, day_id = current_active_day.id, type='one-time', status='active', task_id=new_task_id)

    def set_id_on_insert(new_task: Task):
        new_task.id = new_task_id
    mock_task_repo.insert.side_effect = set_id_on_insert

    task_service.create_task(task_name)

    mock_task_repo.insert.assert_called_once()
    inserted_task = mock_task_repo.insert.call_args[0][0]
    _compare_task_objects_without_id(expected_task, inserted_task)
    assert inserted_task.id == expected_task.id

