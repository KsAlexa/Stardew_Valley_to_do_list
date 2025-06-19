import pytest
from pathlib import Path
from src.repository.day_repository import DayRepository
from src.entities.day_entities import Day
from src.migration import create_database_and_tables

@pytest.fixture
def get_test_db_path(tmp_path: Path) -> str:
    test_db_path = tmp_path / "test_db.sqlite"
    create_database_and_tables(str(test_db_path))
    return str(test_db_path)

@pytest.fixture
def day_repository(get_test_db_path: str) -> DayRepository:
    return DayRepository(connection_string=get_test_db_path)


def test_migration_creates_initial_day(day_repository: DayRepository):
    expected_initial_day = Day(
        day_id=1,
        year = 1,
        season = 'spring',
        number = 1,
        active = True
    )
    actual_initial_day = day_repository.get_by_id(1)
    assert actual_initial_day is not None
    assert actual_initial_day == expected_initial_day

def test_get_active_finds_initial_day(day_repository: DayRepository):
    active_day = day_repository.get_active()
    assert active_day is not None
    assert active_day.id == 1
    assert active_day.active is True

def test_insert_and_get_by_id(day_repository: DayRepository):
    day_to_insert = Day(
        year = 1,
        season = 'autumn',
        number = 13,
        active = False
    )
    day_repository.insert(day_to_insert)
    assert day_to_insert.id is not None

    day_from_bd = day_repository.get_by_id(day_to_insert.id)
    assert day_from_bd is not None
    assert day_from_bd == day_to_insert
