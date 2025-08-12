import pytest
from typing import Tuple, Callable

from service_client import ServiceClient
from helpers import assert_task_data, assert_day_data
from src.api.handlers_models import *


# 1. Установить день на 27 число сезона с 3мя задачами.
#    Устанавливается и проверяется фикстурой day_with_three_tasks_factory:
#     ОР: День создан с корректными параметрами, 3 корректные задачи: 1 однодневная активная, 1 однодневная завершенная, 1 ежедневная.
# 2. Перелистнуть день.
#    ОР: Номер дня увеличился на 1 (28), сезон и год не изменились. Однодневная активная перемещена в список выполненных задач, остальные ее параметры не изменились, ежедневная осталась в текущем дне.
def test_set_next_day_within_month(
    service_client: ServiceClient,
    day_with_three_tasks_factory: Callable[[SetCurrentDayRequest], tuple[CurrentStateResponse, TaskResponse, TaskResponse, TaskResponse]],
):
    initial_year = 1
    initial_season = DaySeason.spring
    initial_number = 27

    active_day_state, active_one_time_task, completed_one_time_task, daily_task = day_with_three_tasks_factory(
        SetCurrentDayRequest(year=initial_year, season=initial_season, number=initial_number)
    )

    state_after_next = service_client.set_next_day()
    day_after_next = state_after_next.current_day_info

    assert_day_data(
        day_after_next,
        expected_year=initial_year,
        expected_season=initial_season,
        expected_number=initial_number + 1,
        expected_active=True,
        expected_tasks=[
            {
                'id': daily_task.id,
                'name': daily_task.name,
                'type': TaskType.daily,
                'status': TaskStatus.active,
                'day_id': day_after_next.id
            }
        ]
    )

    initially_completed_task = next(task for task in state_after_next.all_completed_tasks if task.id == completed_one_time_task.id)
    assert_task_data(
        initially_completed_task,
        expected_id=completed_one_time_task.id,
        expected_name=completed_one_time_task.name,
        expected_type=TaskType.one_time,
        expected_status=TaskStatus.completed,
        expected_day_id=active_day_state.current_day_info.id
    )

    completed_task_after_next = next(task for task in state_after_next.all_completed_tasks if task.id == active_one_time_task.id)
    assert_task_data(
        completed_task_after_next,
        expected_id=active_one_time_task.id,
        expected_name=active_one_time_task.name,
        expected_type=TaskType.one_time,
        expected_status=TaskStatus.completed,
        expected_day_id=active_day_state.current_day_info.id
    )

