import pytest
from unittest.mock import MagicMock
from src import errors
from src.services.task_service import TaskService
from src.entities.task_entities import Task
from src.entities.day_entities import Day
from src.migration import create_database_and_tables
from pathlib import Path
from src.repository import task_repository


@pytest.fixture
def get_test_db_path(tmp_path: Path) -> str:
    test_db_path = tmp_path / "test_day_db.sqlite"
    create_database_and_tables(str(test_db_path))
    return str(test_db_path)


@pytest.fixture
def task_repo(get_test_db_path: str) -> task_repository.TaskRepository:
    return task_repository.TaskRepository(get_test_db_path)


@pytest.fixture
def mock_day_service():
    return MagicMock()


@pytest.fixture
def active_day():
    return Day(year=1, season='spring', number=1, active=True, day_id=1)


@pytest.fixture
def tasks_data_in_db():
    return [
        Task(name='One-time active task 1', day_id=1, type='one-time', status='active', task_id=3),
        Task(name='Daily task 1', day_id=1, type='daily', status='active', task_id=2),
        Task(name='One-time active task 2', day_id=3, type='one-time', status='active', task_id=5),
        Task(name='Daily task 2', day_id=3, type='daily', status='active', task_id=6),
        Task(name='One-time completed task 1', day_id=1, type='one-time', status='completed', task_id=11),
        Task(name='One-time completed task 2', day_id=6, type='one-time', status='completed', task_id=7)
    ]


@pytest.fixture
def task_service(task_repo: task_repository.TaskRepository, mock_day_service: MagicMock) -> TaskService:
    return TaskService(task_repo, mock_day_service)


@pytest.fixture
def task_service_with_tasks_in_db(task_repo: task_repository.TaskRepository,
                                  mock_day_service: MagicMock,
                                  tasks_data_in_db) -> TaskService:
    for task in tasks_data_in_db:
        task_repo.insert(task)
    return TaskService(task_repo, mock_day_service)


def test_create_task_success(task_service, mock_day_service, active_day):
    mock_day_service.get_active.return_value = active_day
    task_name = 'New test task'

    created_task = task_service.create_task(task_name)

    assert created_task.name == task_name
    assert created_task.day_id == active_day.id
    assert created_task.type == 'one-time'
    assert created_task.status == 'active'
    assert created_task.id is not None


def test_create_existent_task_fails(task_service_with_tasks_in_db, mock_day_service, active_day):
    mock_day_service.get_active.return_value = active_day

    existent_task_name = 'One-time active task 1'

    with pytest.raises(errors.DuplicateTaskNameException) as exc_info:
        task_service_with_tasks_in_db.create_task(existent_task_name)

    assert "already exists" in str(exc_info.value)


def test_get_all_by_day_id(task_service_with_tasks_in_db, tasks_data_in_db):
    day_id = 1
    expected_tasks = [task for task in tasks_data_in_db if task.day_id == day_id]

    tasks = task_service_with_tasks_in_db.get_all_by_day_id(day_id)

    assert len(tasks) == len(expected_tasks)
    task_names = {task.name for task in tasks}
    expected_names = {task.name for task in expected_tasks}
    assert task_names == expected_names


def test_get_all_completed(task_service_with_tasks_in_db, tasks_data_in_db):
    expected_completed = [task for task in tasks_data_in_db if task.status == 'completed']

    completed_tasks = task_service_with_tasks_in_db.get_all_completed()

    assert len(completed_tasks) == len(expected_completed)
    completed_names = {task.name for task in completed_tasks}
    expected_names = {task.name for task in expected_completed}
    assert completed_names == expected_names


@pytest.mark.parametrize(
    'initial_type, initial_status, operation, expected_type, expected_status',
    [
        ('one-time', 'active', 'make_completed', 'one-time', 'completed'),
        ('one-time', 'completed', 'make_active', 'one-time', 'active'),  
        ('one-time', 'active', 'make_daily', 'daily', 'active'),
        ('daily', 'active', 'make_one_time', 'one-time', 'active'),
    ],
    ids=['complete_task', 'activate_task', 'make_daily', 'make_one_time']
)
def test_task_state_changes(task_service, mock_day_service, active_day,
                                        initial_type, initial_status, operation, 
                                        expected_type, expected_status):
    mock_day_service.get_active.return_value = active_day

    task = Task(name='Test task', day_id=active_day.id, type=initial_type, status=initial_status)
    task_service.task_repository.insert(task)

    if operation == 'make_completed':
        updated_task = task_service.make_completed(task.id)
    elif operation == 'make_active':
        updated_task = task_service.make_active(task.id)
    elif operation == 'make_daily':
        updated_task = task_service.make_daily(task.id)
    elif operation == 'make_one_time':
        updated_task = task_service.make_one_time(task.id)

    assert updated_task.type == expected_type
    assert updated_task.status == expected_status
    assert updated_task.name == task.name

    db_task = task_service.task_repository.get_by_id(task.id)
    assert db_task.type == expected_type
    assert db_task.status == expected_status


def test_edit_name(task_service, mock_day_service, active_day):
    mock_day_service.get_active.return_value = active_day

    original_name = 'Original task name'
    new_name = 'Updated task name'
    task = Task(name=original_name, day_id=active_day.id, type='one-time', status='active')
    task_service.task_repository.insert(task)

    updated_task = task_service.edit_name(task.id, new_name)

    assert updated_task.name == new_name
    assert updated_task.type == task.type
    assert updated_task.status == task.status

    db_task = task_service.task_repository.get_by_id(task.id)
    assert db_task.name == new_name


@pytest.mark.parametrize(
    'task_day_id, active_day_id, should_raise_error',
    [
        (1, 1, False),
        (1, 2, True),
    ],
    ids=['task_in_active_day', 'task_not_in_active_day']
)
def test_task_operations_check_active_day(task_service, mock_day_service,
                                                      task_day_id, active_day_id, should_raise_error):
    active_day = Day(year=1, season='spring', number=1, active=True, day_id=active_day_id)
    mock_day_service.get_active.return_value = active_day

    task = Task(name='Test task', day_id=task_day_id, type='one-time', status='active')
    task_service.task_repository.insert(task)
    
    if should_raise_error:
        with pytest.raises(errors.TaskNotInActiveDayError):
            task_service.make_completed(task.id)
    else:
        updated_task = task_service.make_completed(task.id)
        assert updated_task.status == 'completed'

#def test_rename_task_from_another_day_should_fail()
#def test_complete_task_from_another_day_should_fail()
#def test_make_daily_task_from_another_day_should_fail()
#def test_make_one_time_task_from_another_day_should_fail()