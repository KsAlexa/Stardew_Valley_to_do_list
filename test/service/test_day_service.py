import pytest
from unittest.mock import MagicMock, call, ANY
from src import errors
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
def mock_day_repo():
    return MagicMock()


@pytest.fixture
def mock_task_repo():
    return MagicMock()


@pytest.fixture
def day_service(mock_day_repo, mock_task_repo):
    return DayService(mock_day_repo, mock_task_repo)


@pytest.fixture
def get_test_db_path(tmp_path: Path) -> str:
    test_db_path = tmp_path / "test_day_db.sqlite"
    create_database_and_tables(str(test_db_path))
    return str(test_db_path)


@pytest.fixture
def day_service_with_db(get_test_db_path: str) -> DayService:
    day_repo = day_repository.DayRepository(get_test_db_path)
    task_repo = task_repository.TaskRepository(get_test_db_path)
    return DayService(day_repo, task_repo)


def test_get_active_day_success(day_service, mock_day_repo):
    expected_day = Day(year=1, season='winter', number=15, active=True, day_id=2)
    mock_day_repo.get_active.return_value = expected_day

    active_day = day_service.get_active()

    assert active_day == expected_day
    mock_day_repo.get_active.assert_called_once()


def test_get_active_day_of_non_existent_day(day_service, mock_day_repo):
    mock_day_repo.get_active.return_value = None

    with pytest.raises(errors.InternalException) as e_info:
        day_service.get_active()

    assert 'No active day' in str(e_info.value)


def test_set_current_day_new_day(day_service, mock_day_repo):
    new_day_id = 2

    day_service._move_tasks_to_current_day = MagicMock()

    previous_active_day = Day(year=1, season='spring', number=1, active=True, day_id=1)
    mock_day_repo.get_active.return_value = previous_active_day
    mock_day_repo.get_by_attributes.return_value = None

    def set_id_on_insert(new_active_day: Day):
        new_active_day.id = new_day_id

    mock_day_repo.insert.side_effect = set_id_on_insert

    expected_new_day = Day(year=1, season='autumn', number=12, active=True, day_id=new_day_id)

    day_service.set_current_day(year=expected_new_day.year, season=expected_new_day.season,
                                number=expected_new_day.number)

    mock_day_repo.set_activity.assert_called_once_with(previous_active_day.id, False)
    mock_day_repo.get_by_attributes.assert_called_once_with(year=expected_new_day.year, season=expected_new_day.season,
                                                            number=expected_new_day.number)

    mock_day_repo.insert.assert_called_once()
    inserted_day = mock_day_repo.insert.call_args[0][0]
    _compare_day_objects_without_id(inserted_day, expected_new_day)  # если провалится, то проблема в логике DayService
    assert inserted_day.id == expected_new_day.id  # если провалится, то проблема в настройке side_effect

    day_service._move_tasks_to_current_day.assert_called_once_with(previous_active_day.id, expected_new_day.id)


def test_set_current_day_existent_day(day_service, mock_day_repo):
    day_service._move_tasks_to_current_day = MagicMock()

    previous_active_day = Day(year=2, season='winter', number=22, active=True, day_id=7)
    mock_day_repo.get_active.return_value = previous_active_day

    expected_day_from_bd = Day(year=1, season='summer', number=25, active=False, day_id=4)
    mock_day_repo.get_by_attributes.return_value = expected_day_from_bd

    set_activity_expected_calls = [
        call(previous_active_day.id, False),
        call(expected_day_from_bd.id, True)
    ]

    day_service.set_current_day(year=expected_day_from_bd.year, season=expected_day_from_bd.season,
                                number=expected_day_from_bd.number)

    mock_day_repo.get_by_attributes.assert_called_once_with(year=expected_day_from_bd.year,
                                                            season=expected_day_from_bd.season,
                                                            number=expected_day_from_bd.number)
    mock_day_repo.set_activity.assert_has_calls(set_activity_expected_calls, any_order=False)
    assert mock_day_repo.set_activity.call_count == len(set_activity_expected_calls)
    mock_day_repo.insert.assert_not_called()

    day_service._move_tasks_to_current_day.assert_called_once_with(previous_active_day.id, expected_day_from_bd.id)


def test_set_current_day_active_day(day_service, mock_day_repo):
    previous_active_day = Day(year=2, season='spring', number=8, active=True, day_id=5)

    mock_day_repo.get_active.return_value = previous_active_day
    mock_day_repo.get_by_attributes.return_value = previous_active_day

    day_service.set_current_day(year=previous_active_day.year, season=previous_active_day.season,
                                number=previous_active_day.number)

    mock_day_repo.get_active.assert_called_once()
    mock_day_repo.get_by_attributes.assert_called_once_with(year=previous_active_day.year,
                                                            season=previous_active_day.season,
                                                            number=previous_active_day.number)
    mock_day_repo.set_activity.assert_not_called()
    mock_day_repo.insert.assert_not_called()


@pytest.mark.parametrize(
    'year, season, number, expected_error_message',
    [
        ('2', 'spring', 5, 'Year must be a positive integer'),
        (0, 'spring', 1, 'Year must be a positive integer'),
        (-1, 'spring', 1, 'Year must be a positive integer'),
        (2, 2, 5, 'Season must be one of'),
        (1, 'string', 28, 'Season must be one of'),
        (4, '', 27, 'Season must be one of'),
        (2, 'spring', '5', 'Day number must be an integer between 1 and 28'),
        (1, 'spring', 0, 'Day number must be an integer between 1 and 28'),
        (1, 'spring', 29, 'Day number must be an integer between 1 and 28')
    ],
    ids=[
        'str year',
        '0 year',
        'negative year',
        'int season',
        'str not from season list',
        'empty season',
        'str day',
        '0 day',
        '29 day'
    ]
)
def test_set_current_day_invalid_input(day_service, mock_day_repo, year, season, number, expected_error_message):
    mock_day_repo.get_active.return_value = Day(year=1, season='spring', number=1, active=True, day_id=4)
    with pytest.raises(errors.InvalidDayError) as e_info:
        day_service.set_current_day(year, season, number)

    assert expected_error_message in str(e_info.value)


def test_set_current_day_fails_if_no_active_day(day_service, mock_day_repo):
    mock_day_repo.get_active.return_value = None

    with pytest.raises(errors.InternalException) as e_info:
        day_service.set_current_day(year=1, season='spring', number=3)

    assert 'No active day' in str(e_info.value)
    mock_day_repo.insert.assert_not_called()


def test_set_next_day_new_day(day_service, mock_day_repo):
    new_day_id = 5

    day_service._move_tasks_to_current_day = MagicMock()

    previous_active_day = Day(year=1, season='spring', number=1, active=True, day_id=3)
    mock_day_repo.get_active.return_value = previous_active_day

    mock_day_repo.get_by_attributes.return_value = None

    def set_id_on_insert(new_active_day: Day):
        new_active_day.id = new_day_id

    mock_day_repo.insert.side_effect = set_id_on_insert
    expected_next_day = Day(year=previous_active_day.year, season=previous_active_day.season,
                            number=previous_active_day.number + 1, active=True,
                            day_id=new_day_id)

    day_service.set_next_day()

    mock_day_repo.get_active.assert_called_once()
    mock_day_repo.get_by_attributes.assert_called_once_with(year=expected_next_day.year,
                                                            season=expected_next_day.season,
                                                            number=expected_next_day.number)
    mock_day_repo.set_activity.assert_called_once_with(previous_active_day.id, False)

    mock_day_repo.insert.assert_called_once()
    inserted_day = mock_day_repo.insert.call_args[0][0]
    _compare_day_objects_without_id(inserted_day, expected_next_day)
    assert inserted_day.id == expected_next_day.id

    day_service._move_tasks_to_current_day.assert_called_once_with(previous_active_day.id, expected_next_day.id)


def test_set_next_day_existent_day(day_service, mock_day_repo):
    day_service._move_tasks_to_current_day = MagicMock()

    previous_active_day = Day(year=3, season='summer', number=17, active=True, day_id=2)
    mock_day_repo.get_active.return_value = previous_active_day

    expected_day_from_bd = Day(year=previous_active_day.year, season=previous_active_day.season,
                               number=previous_active_day.number + 1, active=False, day_id=3)
    mock_day_repo.get_by_attributes.return_value = expected_day_from_bd

    set_activity_expected_calls = [
        call(previous_active_day.id, False),
        call(expected_day_from_bd.id, True)
    ]

    day_service.set_next_day()

    mock_day_repo.get_active.assert_called_once()
    mock_day_repo.get_by_attributes.assert_called_once_with(year=expected_day_from_bd.year,
                                                            season=expected_day_from_bd.season,
                                                            number=expected_day_from_bd.number)
    mock_day_repo.set_activity.assert_has_calls(set_activity_expected_calls, any_order=False)
    assert mock_day_repo.set_activity.call_count == len(set_activity_expected_calls)
    mock_day_repo.insert.assert_not_called()

    day_service._move_tasks_to_current_day.assert_called_once_with(previous_active_day.id, expected_day_from_bd.id)


@pytest.mark.parametrize(
    'previous_active_day_data, expected_next_day_data',
    [
        (
                {'year': 2, 'season': 'summer', 'number': 28},
                {'year': 2, 'season': 'autumn', 'number': 1},
        ),
        (
                {'year': 2, 'season': 'winter', 'number': 28},
                {'year': 3, 'season': 'spring', 'number': 1},
        )
    ],
    ids=[
        'change_season_on_last_day',
        'change_year_and_season_in_the_end_of_winter'
    ]
)
def test_set_next_day_boundary_transitions(day_service, mock_day_repo, previous_active_day_data,
                                           expected_next_day_data):
    new_day_id = 8

    day_service._move_tasks_to_current_day = MagicMock()

    previous_active_day = Day(**previous_active_day_data, active=True, day_id=7)
    mock_day_repo.get_active.return_value = previous_active_day

    mock_day_repo.get_by_attributes.return_value = None

    def set_id_on_insert(new_active_day: Day):
        new_active_day.id = new_day_id

    mock_day_repo.insert.side_effect = set_id_on_insert
    expected_next_day = Day(**expected_next_day_data, active=True, day_id=new_day_id)

    day_service.set_next_day()

    mock_day_repo.get_active.assert_called_once()
    mock_day_repo.get_by_attributes.assert_called_once_with(**expected_next_day_data)
    mock_day_repo.set_activity.assert_called_once_with(previous_active_day.id, False)

    mock_day_repo.insert.assert_called_once()
    inserted_day = mock_day_repo.insert.call_args[0][0]
    _compare_day_objects_without_id(inserted_day, expected_next_day)
    assert inserted_day.id == expected_next_day.id

    day_service._move_tasks_to_current_day.assert_called_once_with(previous_active_day.id, expected_next_day.id)


def test_set_next_day_fails_if_no_active_day(day_service, mock_day_repo):
    mock_day_repo.get_active.return_value = None

    with pytest.raises(errors.InternalException) as e_info:
        day_service.set_next_day()

    assert 'No active day' in str(e_info.value)
    mock_day_repo.insert.assert_not_called()


def test_move_tasks_to_current_day(day_service, mock_day_repo, mock_task_repo):
    previous_day_id = 1
    new_day_id = 2

    tasks_to_move = [
        Task(name='Watch the news', day_id=previous_day_id, type='one-time', status='active', task_id=10),
        Task(name='Hug the husband', day_id=previous_day_id, type='daily', status='active', task_id=11),
        Task(name='Loot the mines', day_id=previous_day_id, type='one-time', status='active', task_id=12),
        Task(name='Water the garden', day_id=previous_day_id, type='daily', status='active', task_id=13),
        Task(name='Speak with neighbour', day_id=previous_day_id, type='one-time', status='completed', task_id=14)
    ]

    mock_task_repo.get_all_by_day_id.return_value = tasks_to_move

    update_field_expected_calls = [
        call(11, 'day_id', new_day_id),
        call(13, 'day_id', new_day_id),
        call(10, 'status', 'completed'),
        call(12, 'status', 'completed'),
    ]

    day_service._move_tasks_to_current_day(previous_day_id, new_day_id)

    mock_task_repo.get_all_by_day_id.assert_called_once_with(previous_day_id)
    mock_task_repo.update_field.assert_has_calls(update_field_expected_calls, any_order=True)
    assert mock_task_repo.update_field.call_count == len(update_field_expected_calls)


def test_move_tasks_to_current_day_no_tasks(day_service, mock_task_repo):
    previous_day_id = 1
    new_day_id = 2

    tasks_to_move = []

    day_service._move_tasks_to_current_day(previous_day_id, new_day_id)

    mock_task_repo.get_all_by_day_id.assert_called_once_with(previous_day_id)
    mock_task_repo.update_field.assert_not_called()


def test_set_next_day_new_day_integrates_with_task_moving(day_service, mock_day_repo, mock_task_repo):
    new_day_id = 12

    previous_active_day = Day(year=4, season='winter', number=19, active=True, day_id=11)
    mock_day_repo.get_active.return_value = previous_active_day

    mock_day_repo.get_by_attributes.return_value = None

    def set_id_on_insert(new_active_day: Day):
        new_active_day.id = new_day_id

    mock_day_repo.insert.side_effect = set_id_on_insert
    expected_next_day = Day(year=previous_active_day.year, season=previous_active_day.season,
                            number=previous_active_day.number + 1, active=True, day_id=new_day_id)

    tasks = [
        Task(name='Test Task1', day_id=previous_active_day.id, type='daily', status='active', task_id=1),
        Task(name='Test Task2', day_id=previous_active_day.id, type='one-time', status='active', task_id=2),
        Task(name='Test Task3', day_id=previous_active_day.id, type='one-time', status='completed', task_id=3)
    ]
    mock_task_repo.get_all_by_day_id.return_value = tasks

    update_field_expected_calls = [
        call(1, 'day_id', new_day_id),
        call(2, 'status', 'completed')
    ]

    day_service.set_next_day()

    mock_day_repo.get_active.assert_called_once()
    mock_day_repo.get_by_attributes.assert_called_once_with(year=expected_next_day.year,
                                                            season=expected_next_day.season,
                                                            number=expected_next_day.number)
    mock_day_repo.set_activity.assert_called_once_with(previous_active_day.id, False)

    mock_day_repo.insert.assert_called_once()
    inserted_day = mock_day_repo.insert.call_args[0][0]
    _compare_day_objects_without_id(inserted_day, expected_next_day)
    assert inserted_day.id == expected_next_day.id

    mock_task_repo.get_all_by_day_id.assert_called_once_with(previous_active_day.id)
    mock_task_repo.update_field.assert_has_calls(update_field_expected_calls, any_order=True)
    assert mock_task_repo.update_field.call_count == len(update_field_expected_calls)

# horizontal integration:
# 1. test_set_next_day_new_day_integrates_with_task_moving()
# 2. test_set_next_day_existent_day_integrates_with_task_moving()
# 3. test_set_current_day_new_day_integrates_with_task_moving()
# 4. test_set_current_day_existent_day_integrates_with_task_moving()
# vertical integration:
# 5. test_get_active_day_returns_correct_data_from_db()
# 6. test_set_current_day_creates_new_day_in_db()
# 7. test_set_next_day_creates_new_day_in_db()
# 8. test_set_current_day_activates_existing_day_in_db()
# 9. test_set_next_day_activates_existing_day_in_db()
# 10. test_set_current_day_fails_on_invalid_input()
# 11. test_set_current_day_updates_tasks_in_db()
# 12. test_set_next_day_updates_tasks_in_db()
# оставлю 1, 4, 5, (6 и 11 объединить), 8, 10

def test_set_current_day_existent_day_integrates_with_task_moving(day_service, mock_day_repo, mock_task_repo):
    previous_active_day = Day(year=1, season='autumn', number=9, active=True, day_id=2)
    mock_day_repo.get_active.return_value = previous_active_day

    expected_day_from_bd = Day(year=1, season='autumn', number=13, active=False, day_id=6)
    mock_day_repo.get_by_attributes.return_value = expected_day_from_bd

    set_activity_expected_calls = [
        call(previous_active_day.id, False),
        call(expected_day_from_bd.id, True)
    ]

    tasks = [
        Task(name='Test Task1', day_id=previous_active_day.id, type='daily', status='active', task_id=3),
        Task(name='Test Task2', day_id=previous_active_day.id, type='one-time', status='active', task_id=2),
        Task(name='Test Task3', day_id=previous_active_day.id, type='one-time', status='completed', task_id=6)
    ]
    mock_task_repo.get_all_by_day_id.return_value = tasks

    update_field_expected_calls = [
        call(3, 'day_id', expected_day_from_bd.id),
        call(2, 'status', 'completed')
    ]

    day_service.set_current_day(year=expected_day_from_bd.year, season=expected_day_from_bd.season,
                                number=expected_day_from_bd.number)

    mock_day_repo.get_by_attributes.assert_called_once_with(year=expected_day_from_bd.year,
                                                            season=expected_day_from_bd.season,
                                                            number=expected_day_from_bd.number)
    mock_day_repo.set_activity.assert_has_calls(set_activity_expected_calls, any_order=False)
    assert mock_day_repo.set_activity.call_count == len(set_activity_expected_calls)
    mock_day_repo.insert.assert_not_called()

    mock_task_repo.get_all_by_day_id.assert_called_once_with(previous_active_day.id)
    mock_task_repo.update_field.assert_has_calls(update_field_expected_calls, any_order=True)
    assert mock_task_repo.update_field.call_count == len(update_field_expected_calls)


def test_get_active_day_returns_correct_data_from_db(day_service_with_db):
    expected_initial_active_day = Day(year=1, season='spring', number=1, active=True, day_id=1)

    active_day = day_service_with_db.get_active()
    assert active_day is not None
    _compare_day_objects_without_id(active_day, expected_initial_active_day)
    assert active_day.id == expected_initial_active_day.id

# def test_set_current_day_activates_existing_day_in_db(day_service_with_db):
# def test_set_current_day_fails_on_invalid_input(day_service_with_db):
# def test_set_current_day_creates_new_day_in_db_and_updates_tasks_in_db(day_service_with_db):
