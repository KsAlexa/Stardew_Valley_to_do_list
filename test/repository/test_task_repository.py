import pytest
import sqlite3
from pathlib import Path

from src.repository.task_repository import TaskRepository
from src.entities.task_entities import Task
from src.migration import create_database_and_tables

# TODO: создать def compare_tasks_without_id  везде где сравниваю объекты заменить
@pytest.fixture
def get_test_db_path(tmp_path: Path) -> str:
    test_db_path = tmp_path / "test_task_db.sqlite"
    create_database_and_tables(str(test_db_path))
    return str(test_db_path)


@pytest.fixture
def test_repo(get_test_db_path: str) -> TaskRepository:
    return TaskRepository(connection_string=get_test_db_path)


@pytest.fixture
def repo_with_one_task(test_repo: TaskRepository) -> TaskRepository:
    task = Task(name='Watch the news', day_id=1, type='daily', status='active')
    test_repo.insert(task)
    return test_repo


@pytest.fixture
def repo_with_two_active_daily_tasks(test_repo: TaskRepository) -> TaskRepository:
    tasks = [
        Task(name='Hug the husband', day_id=1, type='daily', status='active'),
        Task(name='Feed animals', day_id=1, type='daily', status='active')
    ]
    for task in tasks:
        test_repo.insert(task)
    return test_repo

@pytest.fixture
def repo_with_two_completed_one_time_tasks(test_repo: TaskRepository) -> TaskRepository:
    tasks = [
        Task(name='Hug the husband', day_id=2, type='one-time', status='completed'),
        Task(name='Feed animals', day_id=2, type='one-time', status='completed')
    ]
    for task in tasks:
        test_repo.insert(task)
    return test_repo

@pytest.fixture
def repo_with_multiple_tasks(test_repo: TaskRepository) -> tuple[TaskRepository, list[Task]]:
    tasks = [
        Task(name='Loot the mines', day_id=5, type='one-time', status='active'),
        Task(name='Water the garden', day_id=3, type='daily', status='active'),
        Task(name='Make the wine', day_id=3, type='one-time', status='active'),
        Task(name='Craft items', day_id=4, type='one-time', status='active'),
        Task(name='Check the mail', day_id=3, type='daily', status='completed'),
        Task(name='Speak with neighbour', day_id=4, type='daily', status='completed')
    ]
    for task in tasks:
        test_repo.insert(task)
    return test_repo, tasks


def test_insert_and_get_by_id(test_repo: TaskRepository):
    task_to_insert = Task(name='Buy the seeds', day_id=2, type='one-time', status='active')
    test_repo.insert(task_to_insert)
    task_from_bd = test_repo.get_by_id(1)
    assert task_from_bd is not None, 'Task was not created'
    assert task_from_bd == task_to_insert, 'Task from DB is incorrect'


def test_get_by_id_of_non_existent_task(repo_with_two_active_daily_tasks: TaskRepository):
    assert repo_with_two_active_daily_tasks.get_by_id(3) is None, 'Should return None if no day with such id'


def test_insert_existent_task_does_nothing(repo_with_one_task: TaskRepository):
    task_in_bd = repo_with_one_task.get_by_id(1)
    assert task_in_bd is not None, 'Task was not created'
    with sqlite3.connect(repo_with_one_task.connection_string) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tasks")
        count_before_conflict = cursor.fetchone()[0]
    assert count_before_conflict == 1, 'Task was not created'
    conflict_task = Task(name='Watch the news', day_id=2, type='one-time', status='completed')

    try:
        repo_with_one_task.insert(conflict_task)
    except Exception as e:
        pytest.fail(f'insert() of existent task got an Exception "{e}", but it shouldn\'t happen')

    with sqlite3.connect(repo_with_one_task.connection_string) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM days")
        count_after_conflict = cursor.fetchone()[0]
    assert count_after_conflict == count_before_conflict, 'The number of lines has changed'
    task_in_bd_after_conflict = repo_with_one_task.get_by_id(1)
    assert task_in_bd_after_conflict is not None, 'Task after conflict was not found'
    assert task_in_bd_after_conflict.day_id == task_in_bd.day_id, 'Task after conflict changed his day_id'
    assert task_in_bd_after_conflict.type == task_in_bd.type, 'Task after conflict changed his type'
    assert task_in_bd_after_conflict.status == task_in_bd.status, 'Task after conflict changed his status'


def test_get_all_by_day_id(repo_with_multiple_tasks: tuple[TaskRepository, list[Task]]):
    repo, tasks_in_bd = repo_with_multiple_tasks
    expected_tasks_list = []
    for task in tasks_in_bd:
        if task.day_id == 3:
            expected_tasks_list.append(task)
    list_of_found_tasks = repo.get_all_by_day_id(3)
    sorted_expected_task_list = sorted(expected_tasks_list, key=lambda task: task.name)
    sorted_list_of_found_tasks = sorted(list_of_found_tasks, key=lambda task: task.name)
    assert len(list_of_found_tasks) == len(expected_tasks_list), 'Number of found tasks is incorrect'
    assert sorted_expected_task_list == sorted_list_of_found_tasks, 'Objects of found tasks are incorrect'


def test_get_all_by_day_id_of_non_existent_day(repo_with_one_task: TaskRepository):
    expected_tasks_list = []
    list_of_found_tasks = repo_with_one_task.get_all_by_day_id(666)
    assert len(list_of_found_tasks) == len(expected_tasks_list), 'Expected an empty list'


def test_update_field(repo_with_one_task: TaskRepository):
    original_task = repo_with_one_task.get_by_id(1)
    new_name = 'new task name'
    repo_with_one_task.update_field(1, 'name', new_name)
    changed_task = repo_with_one_task.get_by_id(1)
    expected_changed_task = Task(
        name=new_name,
        day_id=original_task.day_id,
        type=original_task.type,
        status=original_task.status
    )
    assert changed_task is not None, 'Can\'t find the changed task'
    assert changed_task.id == original_task.id, 'Task changed its id'
    assert changed_task == expected_changed_task, 'Changed name is incorrect or other fields were changed'


def test_update_field_of_non_existent_task(repo_with_one_task: TaskRepository):
    task_in_bd = repo_with_one_task.get_by_id(1)
    new_name = 'new task name'
    try:
        repo_with_one_task.update_field(666, 'name', new_name)
    except Exception as e:
        pytest.fail('Updating field of non existent task got an exception but it shouldn\'t happen')
    task_in_bd_after_function_call = repo_with_one_task.get_by_id(1)
    assert task_in_bd_after_function_call is not None, 'Task was deleted'
    assert task_in_bd_after_function_call == task_in_bd, 'Task in BD was changed'


def test_make_completed(repo_with_two_active_daily_tasks: TaskRepository):
    task1 = repo_with_two_active_daily_tasks.get_by_id(1)
    task2 = repo_with_two_active_daily_tasks.get_by_id(2)
    new_status = 'completed'
    repo_with_two_active_daily_tasks.make_completed(1)
    task1_after_completed = repo_with_two_active_daily_tasks.get_by_id(1)
    task2_after_function_call = repo_with_two_active_daily_tasks.get_by_id(2)
    expected_task_after_completed = Task(
        name=task1.name,
        day_id=task1.day_id,
        type=task1.type,
        status=new_status
    )
    assert task1_after_completed is not None, 'Completed task was deleted'
    assert task2_after_function_call is not None, 'The neighboring was deleted'
    assert task2_after_function_call == task2, 'The neighboring task has changed'
    assert task1_after_completed.id == task1.id, 'Task changed its id'
    assert task1_after_completed == expected_task_after_completed, 'Task isn\'t completed or other fields were changed'


def test_make_one_time(repo_with_two_active_daily_tasks: TaskRepository):
    task1 = repo_with_two_active_daily_tasks.get_by_id(1)
    task2 = repo_with_two_active_daily_tasks.get_by_id(2)
    new_type = 'one-time'
    repo_with_two_active_daily_tasks.make_one_time(2)
    task1_after_function_call = repo_with_two_active_daily_tasks.get_by_id(1)
    task2_after_changing = repo_with_two_active_daily_tasks.get_by_id(2)
    expected_task_after_changing = Task(
        name=task2.name,
        day_id=task2.day_id,
        type=new_type,
        status=task2.status
    )
    assert task1_after_function_call is not None, 'The neighboring was deleted'
    assert task2_after_changing is not None, 'Changed task was deleted'
    assert task1_after_function_call == task1, 'The neighboring task has changed'
    assert task2_after_changing.id == task2.id, 'Task changed its id'
    assert task2_after_changing == expected_task_after_changing, 'Task isn\'t one-time or other fields were changed'


def test_make_daily(repo_with_two_completed_one_time_tasks: TaskRepository):
    task1 = repo_with_two_completed_one_time_tasks.get_by_id(1)
    task2 = repo_with_two_completed_one_time_tasks.get_by_id(2)
    new_type = 'daily'
    repo_with_two_completed_one_time_tasks.make_daily(1)
    task1_after_changed = repo_with_two_completed_one_time_tasks.get_by_id(1)
    task2_after_function_call = repo_with_two_completed_one_time_tasks.get_by_id(2)
    expected_task_after_changed = Task(
        name=task1.name,
        day_id=task1.day_id,
        type=new_type,
        status=task1.status
    )
    assert task1_after_changed is not None, 'Changed task was deleted'
    assert task2_after_function_call is not None, 'The neighboring was deleted'
    assert task2_after_function_call == task2, 'The neighboring task has changed'
    assert task1_after_changed.id == task1.id, 'Task changed its id'
    assert task1_after_changed == expected_task_after_changed, 'Task isn\'t daily or other fields were changed'


def test_make_active(repo_with_two_completed_one_time_tasks: TaskRepository):
    task1 = repo_with_two_completed_one_time_tasks.get_by_id(1)
    task2 = repo_with_two_completed_one_time_tasks.get_by_id(2)
    new_status = 'active'
    new_day_id = 90
    repo_with_two_completed_one_time_tasks.make_active(2, new_day_id)
    task1_after_function_call = repo_with_two_completed_one_time_tasks.get_by_id(1)
    task2_after_activating = repo_with_two_completed_one_time_tasks.get_by_id(2)
    expected_task_after_activating = Task(
        name=task2.name,
        day_id=new_day_id,
        type=task2.type,
        status=new_status
    )
    assert task1_after_function_call is not None, 'The neighboring was deleted'
    assert task2_after_activating is not None, 'Activated task was deleted'
    assert task1_after_function_call == task1, 'The neighboring task has changed'
    assert task2_after_activating.id == task2.id, 'Task changed its id'
    assert task2_after_activating == expected_task_after_activating, 'Task isn\'t active or other fields were changed'
