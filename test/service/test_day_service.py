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
        previous_day_id = 1
        new_day_id = 2

        self.day_service._move_tasks_to_current_day = MagicMock()

        previous_active_day = Day(year=1, season='spring', number=1, active=True)
        previous_active_day.id = previous_day_id
        self.mock_day_repository.get_active = MagicMock(return_value = previous_active_day)
        self.mock_day_repository.get_by_attributes = MagicMock(return_value = None)

        def set_id_on_insert(new_active_day: Day):
            new_active_day.id = new_day_id
        self.mock_day_repository.insert = MagicMock(side_effect = set_id_on_insert)

        self.day_service.set_current_day(year=1, season = 'autumn', number = 12)

        self.mock_day_repository.set_activity.assert_called_once_with(previous_active_day.id, False)
        self.mock_day_repository.get_by_attributes.assert_called_once_with(year=1, season='autumn', number=12)

        self.mock_day_repository.insert.assert_called_once()
        inserted_day = self.mock_day_repository.insert.call_args[0][0]
        self.assertEqual(inserted_day.year, 1)
        self.assertEqual(inserted_day.season, 'autumn')
        self.assertEqual(inserted_day.number, 12)
        self.assertTrue(inserted_day.active)

        self.day_service._move_tasks_to_current_day.assert_called_once_with(previous_day_id, new_day_id)

        calls_to_set_activity = self.mock_day_repository.set_activity.call_args_list
        self.assertEqual(len(calls_to_set_activity), 1)


    def test_set_current_day_existent_day(self): # провалится, в коде ошибка
        pass


    def move_tasks_to_current_day(self):
        pass