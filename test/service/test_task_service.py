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
def task_service_with_tasks_in_db(task_repo: task_repository.TaskRepository,
                                  mock_day_service: MagicMock,
                                  tasks_data_in_db) -> TaskService:
    for task in tasks_data_in_db:
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


def test_create_existent_task_fails(task_service_with_tasks_in_db, mock_day_service, active_day, tasks_data_in_db):
    mock_day_service.get_active.return_value = active_day

    existent_task_name = tasks_data_in_db[1].name

    with pytest.raises(errors.DuplicateTaskNameException) as exc_info:
        task_service_with_tasks_in_db.create_task(existent_task_name)

    assert "already exists" in str(exc_info.value)


def test_get_by_id_success(task_service, mock_task_repo):
    task_id = 1
    expected_task = Task(name='Test task', day_id=1, type='one-time', status='active', task_id=task_id)
    mock_task_repo.get_by_id.return_value = expected_task

    result_task = task_service.get_by_id(task_id)

    assert result_task == expected_task
    mock_task_repo.get_by_id.assert_called_once_with(task_id)


def test_get_by_id_of_non_existent_task(task_service, mock_task_repo):
    non_existent_task_id = 999
    mock_task_repo.get_by_id.return_value = None

    with pytest.raises(errors.TaskNotFoundException) as exc_info:
        task_service.get_by_id(non_existent_task_id)

    assert f'Task with id {non_existent_task_id} not found' in str(exc_info.value)
    mock_task_repo.get_by_id.assert_called_once_with(non_existent_task_id)


def test_get_all_by_day_id(task_service_with_tasks_in_db, tasks_data_in_db):
    day_id = tasks_data_in_db[1].day_id
    expected_task_list = [task for task in tasks_data_in_db if task.day_id == day_id]

    tasks = task_service_with_tasks_in_db.get_all_by_day_id(day_id)

    assert len(tasks) == len(expected_task_list)
    assert {task.name for task in tasks} == {task.name for task in expected_task_list}


def test_get_all_by_day_id_empty_list(task_service_with_tasks_in_db, tasks_data_in_db):
    non_existent_day_id = 999

    tasks = task_service_with_tasks_in_db.get_all_by_day_id(non_existent_day_id)

    assert len(tasks) == 0
    assert tasks == []


def test_get_all_completed(task_service_with_tasks_in_db, tasks_data_in_db):
    expected_completed_tasks = [task for task in tasks_data_in_db if task.status == 'completed']

    result_tasks = task_service_with_tasks_in_db.get_all_completed()

    assert len(result_tasks) == len(expected_completed_tasks)
    assert {task.name for task in result_tasks} == {task.name for task in expected_completed_tasks}


def test_make_completed(task_service, mock_task_repo, mock_day_service, active_day):
    mock_day_service.get_active.return_value = active_day
    task_id = 1
    active_task = Task(name='Test task to complete', day_id=active_day.id, type='one-time', status='active',
                       task_id=task_id)
    expected_completed_task = Task(name=active_task.name, day_id=active_task.id, type=active_task.type,
                                   status='completed', task_id=active_task.id)

    mock_task_repo.get_by_id.side_effect = [active_task, expected_completed_task]

    result_task = task_service.make_completed(task_id)

    mock_day_service.get_active.assert_called_once()
    mock_task_repo.make_completed.assert_called_once_with(task_id)
    assert result_task == expected_completed_task


def test_make_completed_not_one_time_task_raise_exception(task_service, mock_task_repo, mock_day_service, active_day):
    mock_day_service.get_active.return_value = active_day
    task_id = 1
    daily_task = Task(name='Daily task', day_id=active_day.id, type='daily', status='active', task_id=task_id)

    mock_task_repo.get_by_id.return_value = daily_task

    with pytest.raises(errors.InvalidTaskStateException) as exc_info:
        task_service.make_completed(task_id)

    mock_day_service.get_active.assert_called_once()
    assert f'Task with ID {task_id} cannot be completed. Only \'one-time\' tasks can be marked as completed' in str(
        exc_info.value)
    mock_task_repo.make_completed.assert_not_called()


def test_make_completed_already_completed_task_raises_exception(task_service, mock_task_repo, mock_day_service,
                                                                active_day):
    mock_day_service.get_active.return_value = active_day
    task_id = 1
    completed_task = Task(name='Completed task', day_id=active_day.id, type='one-time', status='completed',
                          task_id=task_id)

    mock_task_repo.get_by_id.return_value = completed_task

    with pytest.raises(errors.InvalidTaskStateException) as exc_info:
        task_service.make_completed(task_id)

    mock_day_service.get_active.assert_called_once()
    assert f'Task with ID {task_id} is already completed' in str(exc_info.value)
    mock_task_repo.make_completed.assert_not_called()


def test_make_completed_task_not_in_current_day_raises_exception(task_service, mock_task_repo, mock_day_service,
                                                                 active_day):
    mock_day_service.get_active.return_value = active_day
    task_id = 1
    task_from_other_day = Task(name='Task from other day', day_id=999, type='one-time', status='active',
                               task_id=task_id)

    mock_task_repo.get_by_id.return_value = task_from_other_day

    with pytest.raises(errors.TaskNotInActiveDayError) as exc_info:
        task_service.make_completed(task_id)

    mock_day_service.get_active.assert_called_once()
    assert f'Task with ID {task_id} not found in active day {active_day.id}' in str(exc_info.value)
    mock_task_repo.make_completed.assert_not_called()


def test_make_active(task_service, mock_task_repo, mock_day_service, active_day):
    mock_day_service.get_active.return_value = active_day
    task_id = 1
    completed_task = Task(name='Completed task', day_id=2, type='one-time', status='completed', task_id=task_id)
    expected_activ_task = Task(name='Completed task', day_id=active_day.id, type='one-time', status='active',
                               task_id=task_id)

    mock_task_repo.get_by_id.side_effect = [completed_task, expected_activ_task]

    result_task = task_service.make_active(task_id)

    mock_day_service.get_active.assert_called_once()
    mock_task_repo.make_active.assert_called_once_with(task_id, active_day.id)
    assert result_task == expected_activ_task


def test_make_active_already_active_task_in_current_day_raises_exception(task_service, mock_task_repo, mock_day_service,
                                                                         active_day):
    mock_day_service.get_active.return_value = active_day
    task_id = 1
    already_active_task = Task(name='Active task', day_id=active_day.id, type='one-time', status='active',
                               task_id=task_id)

    mock_task_repo.get_by_id.return_value = already_active_task

    with pytest.raises(errors.InvalidTaskStateException) as exc_info:
        task_service.make_active(task_id)

    mock_day_service.get_active.assert_called_once()
    assert f'Task with ID {task_id} is already active' in str(exc_info.value)
    mock_task_repo.make_active.assert_not_called()


def test_make_daily(task_service, mock_task_repo, mock_day_service, active_day):
    mock_day_service.get_active.return_value = active_day
    task_id = 1
    one_time_task = Task(name='One-time task', day_id=active_day.id, type='one-time', status='active', task_id=task_id)
    expected_daily_task = Task(name=one_time_task.name, day_id=one_time_task.day_id, type='daily',
                               status=one_time_task.status, task_id=one_time_task.id)

    mock_task_repo.get_by_id.side_effect = [one_time_task, expected_daily_task]

    result_task = task_service.make_daily(task_id)

    mock_day_service.get_active.assert_called_once()
    mock_task_repo.make_daily.assert_called_once_with(task_id)
    assert result_task == expected_daily_task


def test_make_daily_already_daily_task_raises_exception(task_service, mock_task_repo, mock_day_service, active_day):
    mock_day_service.get_active.return_value = active_day
    task_id = 1
    daily_task = Task(name='Daily task', day_id=active_day.id, type='daily', status='active', task_id=task_id)

    mock_task_repo.get_by_id.return_value = daily_task

    with pytest.raises(errors.InvalidTaskStateException) as exc_info:
        task_service.make_daily(task_id)

    mock_day_service.get_active.assert_called_once()
    assert f'Task with ID {task_id} is already a daily task' in str(exc_info.value)
    mock_task_repo.make_daily.assert_not_called()


def test_make_daily_completed_task_raises_exception(task_service, mock_task_repo, mock_day_service, active_day):
    mock_day_service.get_active.return_value = active_day
    task_id = 1
    completed_task = Task(name='Completed task', day_id=active_day.id, type='one-time', status='completed',
                          task_id=task_id)

    mock_task_repo.get_by_id.return_value = completed_task

    with pytest.raises(errors.InvalidTaskStateException) as exc_info:
        task_service.make_daily(task_id)

    mock_day_service.get_active.assert_called_once()
    assert f'Task with ID {task_id} is completed' in str(exc_info.value)
    mock_task_repo.make_daily.assert_not_called()


def test_make_daily_task_not_in_current_day_raises_exception(task_service, mock_task_repo, mock_day_service,
                                                             active_day):
    mock_day_service.get_active.return_value = active_day
    task_id = 1
    task_from_other_day = Task(name='Task from other day', day_id=999, type='one-time', status='active', task_id=task_id)

    mock_task_repo.get_by_id.return_value = task_from_other_day

    with pytest.raises(errors.TaskNotInActiveDayError) as exc_info:
        task_service.make_daily(task_id)

    mock_day_service.get_active.assert_called_once()
    assert f'Task with ID {task_id} not found in active day {active_day.id}' in str(exc_info.value)
    mock_task_repo.make_daily.assert_not_called()


def test_make_one_time(task_service, mock_task_repo, mock_day_service, active_day):
    mock_day_service.get_active.return_value = active_day
    task_id = 1
    daily_task = Task(name='Daily task', day_id=active_day.id, type='daily', status='active', task_id=task_id)
    expected_one_time_task = Task(name=daily_task.name, day_id=daily_task.day_id, type='one-time', status=daily_task.status, task_id=daily_task.id)

    mock_task_repo.get_by_id.side_effect = [daily_task, expected_one_time_task]

    result_task = task_service.make_one_time(task_id)

    mock_day_service.get_active.assert_called_once()
    mock_task_repo.make_one_time.assert_called_once_with(task_id)
    assert result_task == expected_one_time_task


def test_make_one_time_already_one_time_task_raises_exception(task_service, mock_task_repo, mock_day_service, active_day):
    mock_day_service.get_active.return_value = active_day
    task_id = 1
    one_time_task = Task(name='One-time task', day_id=active_day.id, type='one-time', status='active', task_id=task_id)

    mock_task_repo.get_by_id.return_value = one_time_task

    with pytest.raises(errors.InvalidTaskStateException) as exc_info:
        task_service.make_one_time(task_id)

    mock_day_service.get_active.assert_called_once()
    assert f'Task with ID {task_id} is already a one-time task' in str(exc_info.value)
    mock_task_repo.make_one_time.assert_not_called()


def test_make_one_time_task_not_in_current_day_raises_exception(task_service, mock_task_repo, mock_day_service,
                                                                active_day):
    mock_day_service.get_active.return_value = active_day
    task_id = 1
    task_from_other_day = Task(name='Task from other day', day_id=999, type='daily', status='active', task_id=task_id)

    mock_task_repo.get_by_id.return_value = task_from_other_day

    with pytest.raises(errors.TaskNotInActiveDayError) as exc_info:
        task_service.make_one_time(task_id)

    mock_day_service.get_active.assert_called_once()
    assert f'Task with ID {task_id} not found in active day {active_day.id}' in str(exc_info.value)
    mock_task_repo.make_one_time.assert_not_called()


def test_edit_name_success(task_service, mock_task_repo, mock_day_service, active_day):
    mock_day_service.get_active.return_value = active_day
    task_id = 1
    new_name = 'New task name'
    task = Task(name='Original task', day_id=active_day.id, type='one-time', status='active', task_id=task_id)
    updated_task = Task(name=new_name, day_id=task.id, type=task.type, status=task.status, task_id=task.id)

    mock_task_repo.get_by_id.side_effect = [task, updated_task]

    result_task = task_service.edit_name(task_id, new_name)

    mock_day_service.get_active.assert_called_once()
    mock_task_repo.edit_name.assert_called_once_with(task_id, new_name)
    assert result_task == updated_task


def test_edit_name_completed_task_raises_exception(task_service, mock_task_repo, mock_day_service, active_day):
    mock_day_service.get_active.return_value = active_day
    task_id = 1
    new_name = 'New task name'
    completed_task = Task(name='Completed task', day_id=active_day.id, type='one-time', status='completed',
                          task_id=task_id)

    mock_task_repo.get_by_id.return_value = completed_task

    with pytest.raises(errors.InvalidTaskStateException) as exc_info:
        task_service.edit_name(task_id, new_name)

    mock_day_service.get_active.assert_called_once()
    assert f'Task with ID {task_id} is completed. To edit it, make it active first' in str(exc_info.value)
    mock_task_repo.edit_name.assert_not_called()


def test_edit_name_task_not_in_current_day_raises_exception(task_service, mock_task_repo, mock_day_service, active_day):
    mock_day_service.get_active.return_value = active_day
    task_id = 1
    new_name = 'New task name'
    task_from_other_day = Task(name='Task from other day', day_id=2, type='daily', status='active', task_id=task_id)

    mock_task_repo.get_by_id.return_value = task_from_other_day

    with pytest.raises(errors.TaskNotInActiveDayError) as exc_info:
        task_service.edit_name(task_id, new_name)

    mock_day_service.get_active.assert_called_once()
    assert f'Task with ID {task_id} not found in active day {active_day.id}' in str(exc_info.value)
    mock_task_repo.edit_name.assert_not_called()
