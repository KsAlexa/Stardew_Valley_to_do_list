import pytest
import sqlite3
from pathlib import Path

from src.errors import MultipleActiveDaysException
from src.repository.day_repository import DayRepository
from src.entities.day_entities import Day
from src.migration import create_database_and_tables


@pytest.fixture
def get_test_db_path(tmp_path: Path) -> str:
    test_db_path = tmp_path / "test_day_db.sqlite"
    create_database_and_tables(str(test_db_path))
    return str(test_db_path)


@pytest.fixture
def repo_with_initial_day(get_test_db_path: str) -> DayRepository:
    return DayRepository(connection_string=get_test_db_path)


@pytest.fixture
def repo_with_multiple_days_data(repo_with_initial_day: DayRepository) -> DayRepository:
    days = [
        Day(year=1, season='spring', number=2, active=False),
        Day(year=1, season='summer', number=15, active=False),
        Day(year=1, season='summer', number=28, active=False),
        Day(year=4, season='autumn', number=4, active=False),
        Day(year=3, season='winter', number=27, active=False),
    ]
    for day in days:
        repo_with_initial_day.insert(day)
    return repo_with_initial_day


def test_migration_is_idempotent(tmp_path: Path):
    test_db_path = str(tmp_path / "idempotent_test.sqlite")
    create_database_and_tables(test_db_path)
    with sqlite3.connect(test_db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM days")
        count1 = cursor.fetchone()[0]
    assert count1 == 1, 'Initial day was not created'
    create_database_and_tables(test_db_path)
    with sqlite3.connect(test_db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM days")
        count2 = cursor.fetchone()[0]
    assert count2 == 1, 'Initial day was duplicated'


def test_migration_creates_initial_day(repo_with_initial_day: DayRepository):
    expected_initial_day = Day(
        day_id=1,
        year=1,
        season='spring',
        number=1,
        active=True
    )
    actual_initial_day = repo_with_initial_day.get_by_id(1)
    assert actual_initial_day is not None, 'Initial day was not created'
    assert actual_initial_day == expected_initial_day, 'Initial day is incorrect'


def test_get_active_finds_initial_day(repo_with_initial_day: DayRepository):
    initial_active_day = repo_with_initial_day.get_active()
    assert initial_active_day is not None, 'Initial day was not created'
    assert initial_active_day.id == 1, f'Expected id=1, got {initial_active_day.id} instead'
    assert initial_active_day.active is True, 'Initial day isn\'t active'


def test_deactivate_initial_day(repo_with_initial_day: DayRepository):
    initial_active_day = repo_with_initial_day.get_active()
    repo_with_initial_day.set_activity(initial_active_day.id, False)
    assert repo_with_initial_day.get_active() is None, 'Initial day is still active'
    deactivated_day = repo_with_initial_day.get_by_id(initial_active_day.id)
    assert deactivated_day is not None, 'Deactivated day was not found'
    assert deactivated_day.active is False, 'Day activity was not changed'


def test_insert_and_get_by_id(repo_with_initial_day: DayRepository):
    day_to_insert = Day(year=1, season='autumn', number=13, active=False)
    repo_with_initial_day.insert(day_to_insert)
    assert day_to_insert.id is not None, 'Day was not created'

    day_from_db = repo_with_initial_day.get_by_id(day_to_insert.id)
    assert day_from_db is not None, 'Day was not created'
    assert day_from_db == day_to_insert, 'Day from DB is incorrect'


def test_get_by_id_of_non_existent_day(repo_with_initial_day: DayRepository):
    assert repo_with_initial_day.get_by_id(2) is None, 'Should return None if no day with such id'


def test_insert_existent_day_does_nothing(repo_with_initial_day: DayRepository):
    initial_day = repo_with_initial_day.get_by_id(1)
    assert initial_day is not None, 'Initial day was not created'
    with sqlite3.connect(repo_with_initial_day.connection_string) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM days")
        count_before_conflict = cursor.fetchone()[0]
    assert count_before_conflict == 1, 'Initial day was not created'
    conflict_day = Day(
        year=1,
        season='spring',
        number=1,
        active=False
    )

    try:
        repo_with_initial_day.insert(conflict_day)
    except Exception as e:
        pytest.fail(f'insert() of existent day got an Exception "{e}", but it shouldn\'t happen')

    with sqlite3.connect(repo_with_initial_day.connection_string) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM days")
        count_after_conflict = cursor.fetchone()[0]
    assert count_after_conflict == count_before_conflict, 'The number of lines has changed'

    initial_day_after_conflict = repo_with_initial_day.get_by_attributes(
        year=initial_day.year,
        season=initial_day.season,
        number=initial_day.number,
    )
    assert initial_day_after_conflict is not None, 'Day after conflict was not found'
    assert initial_day_after_conflict.id == initial_day.id, 'Day after conflict changed its id'
    assert initial_day_after_conflict.active is True, 'Day after conflict changed its activity'


def test_get_day_by_attributes(repo_with_multiple_days_data: DayRepository):
    search_year, search_season, search_day = 1, 'summer', 28
    day_from_db = repo_with_multiple_days_data.get_by_attributes(search_year, search_season, search_day)
    assert day_from_db is not None, f'Day with attributes {search_year}, {search_season}, {search_day} was not found'
    assert day_from_db.year == search_year, 'Day year is incorrect'
    assert day_from_db.season == search_season, 'Day season is incorrect'
    assert day_from_db.number == search_day, 'Day number is incorrect'


def test_get_day_by_attributes_of_non_existent_day(repo_with_multiple_days_data: DayRepository):
    search_year, search_season, search_day = 1, 'summer', 11
    non_existent_day_from_db = repo_with_multiple_days_data.get_by_attributes(search_year, search_season, search_day)
    assert non_existent_day_from_db is None, 'Should return None if no day with such attributes'


def test_get_active_after_changing_active_day(repo_with_multiple_days_data: DayRepository):
    initial_active_day = repo_with_multiple_days_data.get_active()
    day_to_make_activ = repo_with_multiple_days_data.get_by_attributes(year=4, season='autumn', number=4)
    assert day_to_make_activ is not None, 'Day to make activ was not found'
    repo_with_multiple_days_data.set_activity(initial_active_day.id, False)
    repo_with_multiple_days_data.set_activity(day_to_make_activ.id, True)
    new_active_day = repo_with_multiple_days_data.get_active()
    assert new_active_day is not None, 'No active day after changing activity'
    assert new_active_day.id == day_to_make_activ.id, 'Incorrect new active day'


def test_get_active_with_no_active_days(repo_with_initial_day: DayRepository):
    initial_active_day = repo_with_initial_day.get_active()
    repo_with_initial_day.set_activity(initial_active_day.id, False)
    assert repo_with_initial_day.get_active() is None, 'Should return None if no active days'


def test_set_activity_on_non_existent_day(repo_with_initial_day: DayRepository):
    try:
        repo_with_initial_day.set_activity(2, False)
    except Exception as e:
        pytest.fail('Setting activity of non existent day got an exception but it shouldn\'t happen')
    non_existent_day_to_set_activity = repo_with_initial_day.get_by_id(2)
    assert non_existent_day_to_set_activity is None, 'Non existent day was found after setting its activity'
    assert repo_with_initial_day.get_active() is not None, 'Initial day disappeared'
    assert repo_with_initial_day.get_active().active == True, 'Initial day changed its activity'
    assert repo_with_initial_day.get_active().id == 1, 'Initial day changed its id'


def test_get_active_raises_multiple_active_days_exception(repo_with_multiple_days_data: DayRepository):
    day_to_make_activ = repo_with_multiple_days_data.get_by_attributes(year=3, season='winter', number=27)
    assert day_to_make_activ is not None, 'Day to make activ was not found'
    repo_with_multiple_days_data.set_activity(day_to_make_activ.id, True)
    with pytest.raises(MultipleActiveDaysException) as exception_message:
        repo_with_multiple_days_data.get_active()
    assert 'Multiple active days' in str(exception_message.value), 'Exception message missmatch'
