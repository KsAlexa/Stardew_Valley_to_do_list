import pytest
from src.services.day_service import DayService
from src.entities.day_entities import Day
from src.entities.task_entities import Task
from src.migration import create_database_and_tables
from pathlib import Path
from src.repository import day_repository, task_repository

def _compare_day_objects_without_id(day1: Day, day2: Day):
    assert day1.year == day2.year, 'Years do not match'
    assert day1.season == day2.season, 'Seasons do not match'
    assert day1.number == day2.number, 'Numbers do not match'
    assert day1.active == day2.active, 'Activity do not match'

@pytest.fixture
def get_test_db_path(tmp_path: Path) -> str:
    test_db_path = tmp_path / "test_day_db.sqlite"
    create_database_and_tables(str(test_db_path))
    return str(test_db_path)


@pytest.fixture
def day_repo(get_test_db_path: str) -> day_repository.DayRepository:
    return day_repository.DayRepository(get_test_db_path)


@pytest.fixture
def task_repo(get_test_db_path: str) -> task_repository.TaskRepository:
    return task_repository.TaskRepository(get_test_db_path)


@pytest.fixture
def day_service_with_initial_day_in_db(day_repo: day_repository.DayRepository,
                                       task_repo: task_repository.TaskRepository) -> DayService:
    return DayService(day_repo, task_repo)


@pytest.fixture
def day_service_with_multiple_days_in_db(day_repo: day_repository.DayRepository,
                                       task_repo: task_repository.TaskRepository) -> DayService:
    days = [
        Day(year=1, season='spring', number=2, active=False, day_id=2),
        Day(year=1, season='summer', number=15, active=False, day_id=3),
        Day(year=1, season='summer', number=28, active=False, day_id=4),
        Day(year=4, season='autumn', number=4, active=False, day_id=5),
        Day(year=3, season='winter', number=27, active=False, day_id=6),
    ]
    for day in days:
        day_repo.insert(day)
    return DayService(day_repo, task_repo)

def test_get_active_day_returns_correct_data_from_db(day_service_with_initial_day_in_db):
    expected_initial_active_day = Day(year=1, season='spring', number=1, active=True, day_id=1)

    active_day = day_service_with_initial_day_in_db.get_active()
    assert active_day is not None
    _compare_day_objects_without_id(active_day, expected_initial_active_day)
    assert active_day.id == expected_initial_active_day.id


def test_set_current_day_activates_existing_day_in_db(day_service_with_multiple_days_in_db):
    day_year_from_bd, day_season_from_bd, day_number_from_bd = 1, 'summer', 15

    day_service_with_multiple_days_in_db.set_current_day(year=day_year_from_bd, season=day_season_from_bd, number=day_number_from_bd)

    new_active_day = day_service_with_multiple_days_in_db.get_active()
    assert new_active_day.year == day_year_from_bd
    assert new_active_day.season == day_season_from_bd
    assert new_active_day.number == day_number_from_bd
    assert new_active_day.active == True


def test_set_next_day_creates_new_day_and_updates_tasks(day_service_with_initial_day_in_db, day_repo, task_repo):
    initial_day = day_repo.get_active()
    expected_next_day = Day(year=initial_day.year, season=initial_day.season,
                            number=initial_day.number + 1, active=True,
                            day_id=initial_day.id + 1)

    tasks = [
        Task(name='Daily task 1', day_id=initial_day.id, type='daily', status='active'),
        Task(name='Daily task 2', day_id=initial_day.id, type='daily', status='active'),
        Task(name='One-time active task', day_id=initial_day.id, type='one-time', status='active'),
        Task(name='One-time completed task', day_id=initial_day.id, type='one-time', status='completed'),
    ]

    for task in tasks:
        task_repo.insert(task)

    one_time_tasks = [task for task in tasks if task.type == 'one-time']

    day_service_with_initial_day_in_db.set_next_day()

    assert day_repo.get_by_id(initial_day.id).active == False
    new_active_day = day_repo.get_active()
    assert new_active_day is not None
    _compare_day_objects_without_id(new_active_day, expected_next_day)

    new_day_tasks = task_repo.get_all_by_day_id(new_active_day.id)
    daily_tasks = [task for task in new_day_tasks if task.type == 'daily']
    assert len(new_day_tasks) == len(daily_tasks)
    assert new_day_tasks == daily_tasks

    for task in one_time_tasks:
        updated_task = task_repo.get_by_id(task.id)
        assert updated_task.status == 'completed'