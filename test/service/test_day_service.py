import unittest
import pytest
from unittest.mock import MagicMock, call
from src import errors
from src.services.day_service import DayService
from src.entities.day_entities import Day
from src.entities.task_entities import Task

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
    previous_day_id = 1
    new_day_id = 2

    day_service._move_tasks_to_current_day = MagicMock()

    previous_active_day = Day(year=1, season='spring', number=1, active=True)
    previous_active_day.id = previous_day_id
    mock_day_repo.get_active.return_value =  previous_active_day
    mock_day_repo.get_by_attributes.return_value = None

    def set_id_on_insert(new_active_day: Day):
        new_active_day.id = new_day_id
    mock_day_repo.insert.side_effect = set_id_on_insert

    day_service.set_current_day(year=1, season = 'autumn', number = 12)

    mock_day_repo.set_activity.assert_called_once_with(previous_active_day.id, False)
    mock_day_repo.get_by_attributes.assert_called_once_with(year=1, season='autumn', number=12)

    mock_day_repo.insert.assert_called_once()
    inserted_day = mock_day_repo.insert.call_args[0][0]
    expected_day = Day(year=1, season='autumn', number=12, active=True)
    _compare_day_objects_without_id(inserted_day, expected_day)

    day_service._move_tasks_to_current_day.assert_called_once_with(previous_day_id, new_day_id)

    calls_to_set_activity = mock_day_repo.set_activity.call_args_list
    assert len(calls_to_set_activity) == 1


def test_set_current_day_existent_day(day_service, mock_day_repo):
    previous_day_id = 7
    existing_day_id = 4

    day_service._move_tasks_to_current_day = MagicMock()

    previous_active_day = Day(year=2, season='winter', number=22, active=True)
    previous_active_day.id = previous_day_id
    day_from_bd = Day(year=1, season='summer', number=25, active=False)
    day_from_bd.id = existing_day_id
    mock_day_repo.get_active.return_value = previous_active_day
    mock_day_repo.get_by_attributes.return_value = day_from_bd

    set_activity_expected_calls = [
        call(previous_active_day.id, False),
        call(day_from_bd.id, True)
    ]

    day_service.set_current_day(year=1, season = 'summer', number = 25)

    mock_day_repo.get_by_attributes.assert_called_once_with(year=1, season='summer', number=25)
    assert mock_day_repo.set_activity.call_args_list == set_activity_expected_calls
    mock_day_repo.insert.assert_not_called()

    day_service._move_tasks_to_current_day.assert_called_once_with(previous_day_id, existing_day_id)

def test_set_current_day_active_day(day_service, mock_day_repo):
    previous_day_id = 5


    previous_active_day = Day(year=2, season='spring', number=8, active=True)
    previous_active_day.id = previous_day_id

    mock_day_repo.get_active.return_value = previous_active_day
    mock_day_repo.get_by_attributes.return_value = previous_active_day

    day_service.set_current_day(year=2, season='spring', number=8)

    mock_day_repo.get_active.assert_called_once()
    mock_day_repo.get_by_attributes.assert_called_once_with(year=2, season='spring', number=8)
    mock_day_repo.set_activity.assert_not_called()
    mock_day_repo.insert.assert_not_called()


@pytest.mark.parametrize(
    "year, season, number, expected_error_message",
    [
        ('2', 'spring', 5, "Year must be a positive integer"),
        (0, 'spring', 1, "Year must be a positive integer"),
        (-1, 'spring', 1, "Year must be a positive integer"),
        (2, 2, 5, "Season must be one of"),
        (1, 'string', 28, "Season must be one of"),
        (2, 'spring', '5', "Day number must be an integer between 1 and 28"),
        (1, 'spring', 0, "Day number must be an integer between 1 and 28"),
        (1, 'spring', 29, "Day number must be an integer between 1 and 28")
    ]
)

def test_set_current_day_invalid_input(day_service, mock_day_repo, year, season, number, expected_error_message):
    mock_day_repo.get_active.return_value = Day(year = 1, season =  'spring', number = 1,  active = True)
    with pytest.raises(errors.InvalidDayError) as e_info:
        day_service.set_current_day(year, season, number)

    assert expected_error_message in str(e_info.value)


def test_move_tasks_to_current_day(day_service, mock_day_repo, mock_task_repo):
    previous_day_id = 1
    new_day_id = 2

    tasks_to_move = [
        Task(name='Watch the news', day_id=previous_day_id, type='one-time', status='active'),
        Task(name='Hug the husband', day_id=previous_day_id, type='daily', status='active'),
        Task(name='Loot the mines', day_id=previous_day_id, type='one-time', status='active'),
        Task(name='Water the garden', day_id=previous_day_id, type='daily', status='active'),
        Task(name='Speak with neighbour', day_id=previous_day_id, type='one-time', status='completed')
    ]
    for i, task_data in enumerate(tasks_to_move, start=10):
        task_data.id = i

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

def test_set_next_day_new_day(day_service, mock_day_repo):
    # 1.найти активный день get_active.assert_called_once()
    # 2.просчитать год, сезон, день след дня(отловить) get_by_attributes.assert_called_once_with
    # 3.деактивировать пред день set_activity.assert_called_once()
    # 4.найти в бд день с атрибутами след дня .return_value = None
    # 5. создался день с атрибутами след дня, положился в базу .insert.side_effect
    # 6.перенесли задачи _move_tasks_to_current_day.assert_called_once()
    mock_day_repo.get_active.return_value = Day(year = 1, season =  'spring', number = 1,  active = True)
    mock_day_repo.get_by_attributes.return_value = None


def test_set_next_day_existent_day(day_service, mock_day_repo):
    # 1.найти активный день get_active.assert_called_once()
    # 2.просчитать год, сезон, день след дня(отловить) get_by_attributes.assert_called_once_with
    # 3.деактивировать пред день
    # 4.найти в бд день с атрибутами след дня .return_value = Day()
    # 5.активировать день с атрибутами след дня set_activity.call_args_list
    # 6.перенесли задачи _move_tasks_to_current_day.assert_called_once()
    pass

# @pytest.mark.parametrize()
#  переход на след сезон (28 день месяца)
# переход на след сезон (28 день зимы)
def test_set_next_day_boundary_transitions():
    pass