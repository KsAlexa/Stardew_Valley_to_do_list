import unittest
from unittest.mock import MagicMock, call
from src import errors
from src.services.day_service import DayService
from src.entities.day_entities import Day
from src.entities.task_entities import Task


class TestsDayService(unittest.TestCase):
    def setUp(self):
        self.mock_day_repository = MagicMock()
        self.mock_task_repository = MagicMock()

        self.day_service = DayService(self.mock_day_repository, self.mock_task_repository)


    def test_get_active_day_success(self):
        self.mock_day_repository.get_active = MagicMock(
            return_value=Day(year=1, season='winter', number=15, active=True, day_id=2)
        )

        active_day = self.day_service.get_active()
        self.assertEqual(active_day, Day(year=1, season='winter', number=15, active=True, day_id=2))

    def test_get_active_day_of_non_existent_day(self):
        self.mock_day_repository.get_active = MagicMock(
            return_value=None
        )
        with self.assertRaises(errors.InternalException) as e:
            self.day_service.get_active()


    def test_set_current_day_new_day(self):
        previous_active_day = Day(year=1, season='spring', number=1, active=True)
        previous_active_day.id = 1
        self.mock_day_repository.get_active = MagicMock(return_value = previous_active_day)
        self.mock_day_repository.get_by_attributes = MagicMock(return_value = None)

        tasks = [
            Task(name='Watch the news', day_id=1, type='one-time', status='active'),
            Task(name='Hug the husband', day_id=1, type='daily', status='active'),
            Task(name='Loot the mines', day_id=1, type='one-time', status='active'),
            Task(name='Water the garden', day_id=1, type='daily', status='active'),
            Task(name='Speak with neighbour', day_id=1, type='one-time', status='completed')
        ]
        for i, task_data in enumerate(tasks, start = 3):
            task_data.id = i
        self.mock_task_repository.get_all_by_day_id = MagicMock(return_value = tasks)

        def set_id_on_insert(new_active_day: Day):
            new_active_day.id = 2
        self.mock_day_repository.insert = MagicMock(side_effect = set_id_on_insert)

        self.day_service.set_current_day(year=1, season = 'autumn', number = 12)

        self.mock_day_repository.set_activity.assert_called_once_with(previous_active_day.id, False)
        self.mock_day_repository.insert.assert_called_once()
        inserted_day = self.mock_day_repository.insert.call_args[0][0]
        self.assertEqual(inserted_day, Day(year=1, season='autumn', number=12, active=True, day_id=2))
        expected_calls = [
            call(3, 'status', 'completed'),
            call(4, 'day_id', inserted_day.id),
            call(5, 'status', 'completed'),
            call(6, 'day_id', inserted_day.id)
        ]

        self.mock_task_repository.update_field.assert_has_calls(expected_calls, any_order=True)
        self.assertEqual(self.mock_task_repository.update_field.call_count, len(expected_calls))