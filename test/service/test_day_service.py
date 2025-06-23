import unittest
from unittest.mock import MagicMock, call

import pytest

from src import errors
from src.services.day_service import DayService
from src.entities.day_entities import Day
from src.entities.task_entities import Task


class TestsGroup(unittest.TestCase):
    def setUp(self):
        self.mock_day_repository = MagicMock()
        self.mock_task_repository = MagicMock()

        self.day_service = DayService(self.mock_day_repository, self.mock_task_repository)

        self.mock_day_repository.get_active = MagicMock(
            return_value=Day(year=1, season='winter', number=15, active=True, day_id=1)
        )

    def test_get_active_day_success(self):
        active_day = self.day_service.get_active()
        self.assertEqual(active_day, Day(year=1, season='winter', number=15, active=True, day_id=1))

    def test_get_active_day_of_non_existent_day(self):
        self.mock_day_repository.get_active = MagicMock(
            return_value=None
        )
        with self.assertRaises(errors.InternalException) as e:
            self.day_service.get_active()
