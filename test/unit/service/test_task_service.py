import pytest
from unittest.mock import MagicMock
from src import errors
from src.services.task_service import TaskService
from src.entities.task_entities import Task
from src.entities.day_entities import Day


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


def test_create_task(task_service, mock_task_repo, mock_day_service, active_day):
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


def test_create_existent_task_fails(task_service, mock_task_repo, mock_day_service, active_day):
    mock_day_service.get_active.return_value = active_day
    existent_task_name = 'task name conflict'
    mock_task_repo.insert.side_effect = errors.DuplicateTaskNameException('Task with name "{existent_task_name}" already exists')

    with pytest.raises(errors.DuplicateTaskNameException) as exc_info:
        task_service.create_task(existent_task_name)

    assert "already exists" in str(exc_info.value)


def test_get_by_id(task_service, mock_task_repo):
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


def test_get_all_by_day_id(task_service, mock_task_repo):
    day_id = 1
    expected_task_list = [
        Task(name='Task 1', day_id=day_id, type='one-time', status='active', task_id=1),
        Task(name='Task 2', day_id=day_id, type='daily', status='active', task_id=2)
    ]
    mock_task_repo.get_all_by_day_id.return_value = expected_task_list

    tasks = task_service.get_all_by_day_id(day_id)

    assert len(tasks) == len(expected_task_list)
    assert tasks == expected_task_list
    mock_task_repo.get_all_by_day_id.assert_called_once_with(day_id)


def test_get_all_by_day_id_empty_list(task_service, mock_task_repo):
    non_existent_day_id = 999
    mock_task_repo.get_all_by_day_id.return_value = []

    tasks = task_service.get_all_by_day_id(non_existent_day_id)

    assert len(tasks) == 0
    assert tasks == []
    mock_task_repo.get_all_by_day_id.assert_called_once_with(non_existent_day_id)


def test_get_all_completed(task_service, mock_task_repo):
    expected_completed_tasks = [
        Task(name='Completed Task 1', day_id=1, type='one-time', status='completed', task_id=1),
        Task(name='Completed Task 2', day_id=2, type='one-time', status='completed', task_id=2)
    ]
    mock_task_repo.get_all_completed.return_value = expected_completed_tasks

    result_tasks = task_service.get_all_completed()

    assert len(result_tasks) == len(expected_completed_tasks)
    assert result_tasks == expected_completed_tasks
    mock_task_repo.get_all_completed.assert_called_once()


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


def test_edit_name(task_service, mock_task_repo, mock_day_service, active_day):
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


@pytest.mark.parametrize(
    'operation, task_type, task_status, expected_error_message',
    [
        ('make_completed', 'daily', 'active',
         'cannot be completed. Only \'one-time\' tasks can be marked as completed'),
        ('make_completed', 'one-time', 'completed', 'is already completed'),
        ('make_daily', 'daily', 'active', 'is already a daily task'),
        ('make_daily', 'one-time', 'completed', 'is completed'),
        ('make_one_time', 'one-time', 'active', 'is already a one-time task'),
        ('edit_name', 'one-time', 'completed', 'is completed. To edit it, make it active first'),
    ],
    ids=['complete_daily', 'complete_already_completed', 'daily_already_daily', 'daily_completed', 'one_time_already_one_time', 'edit_completed']
)
def test_task_operations_invalid_states(task_service, mock_task_repo, mock_day_service, active_day, operation, task_type, task_status, expected_error_message):
    mock_day_service.get_active.return_value = active_day
    task_id = 1
    invalid_task = Task(name='Invalid task', day_id=active_day.id, type=task_type, status=task_status, task_id=task_id)

    mock_task_repo.get_by_id.return_value = invalid_task

    with pytest.raises(errors.InvalidTaskStateException) as exc_info:
        if operation == 'make_completed':
            task_service.make_completed(task_id)
        elif operation == 'make_daily':
            task_service.make_daily(task_id)
        elif operation == 'make_one_time':
            task_service.make_one_time(task_id)
        elif operation == 'edit_name':
            task_service.edit_name(task_id, 'New name')

    assert expected_error_message in str(exc_info.value)

    if operation == 'make_completed':
        mock_task_repo.make_completed.assert_not_called()
    elif operation == 'make_daily':
        mock_task_repo.make_daily.assert_not_called()
    elif operation == 'make_one_time':
        mock_task_repo.make_one_time.assert_not_called()
    elif operation == 'edit_name':
        mock_task_repo.edit_name.assert_not_called()


@pytest.mark.parametrize(
    'operation',
    ['make_completed', 'make_daily', 'make_one_time', 'edit_name'],
    ids=['complete', 'make_daily', 'make_one_time', 'edit_name']
)
def test_task_operations_not_in_active_day(task_service, mock_task_repo, mock_day_service, active_day, operation):
    mock_day_service.get_active.return_value = active_day
    task_id = 1
    other_day_id = 999
    task_from_other_day = Task(name='Task from other day', day_id=other_day_id, type='one-time', status='active', task_id=task_id)

    mock_task_repo.get_by_id.return_value = task_from_other_day

    with pytest.raises(errors.TaskNotInActiveDayError) as exc_info:
        if operation == 'make_completed':
            task_service.make_completed(task_id)
        elif operation == 'make_daily':
            task_service.make_daily(task_id)
        elif operation == 'make_one_time':
            task_service.make_one_time(task_id)
        elif operation == 'edit_name':
            task_service.edit_name(task_id, 'New name')

    assert f'Task with ID {task_id} not found in active day {active_day.id}' in str(exc_info.value)