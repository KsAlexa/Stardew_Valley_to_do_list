from typing import Dict, Any
from src.api.handlers_models import *

def assert_task_data(
    task_data: Dict[str, Any] | TaskResponse,
    *,
    expected_id: int | None = None,
    expected_name: str,
    expected_type: TaskType = TaskType.one_time,
    expected_status: TaskStatus = TaskStatus.active,
    expected_day_id: int
):
    if isinstance(task_data, dict):
        task = TaskResponse.model_validate(task_data)
    else:
        task = task_data
    
    assert task.name == expected_name
    assert task.type == expected_type
    assert task.status == expected_status
    assert task.day_id == expected_day_id

    if expected_id is not None:
        assert task.id == expected_id


def assert_day_data(
    day_data: Dict[str, Any] | CurrentDayResponse,
    *,
    expected_id: int | None = None,
    expected_year: int,
    expected_season: DaySeason,
    expected_number: int,
    expected_active: bool,
    expected_tasks: list[TaskResponse] | list[dict[str, Any]] | None = None
):
    if isinstance(day_data, dict):
        day = CurrentDayResponse.model_validate(day_data)
    else:
        day = day_data

    assert day.year == expected_year
    assert day.season == expected_season
    assert day.number == expected_number
    assert day.active == expected_active

    if expected_id is not None:
        assert day.id == expected_id

    if expected_tasks is not None:
        assert day.tasks is not None

        for i, task in enumerate(expected_tasks):
            if isinstance(task, dict):
                expected_tasks[i] = TaskResponse.model_validate(task)

        assert len(day.tasks) == len(expected_tasks)
        
        for current_task, expected_task in zip(day.tasks, expected_tasks):
            assert_task_data(
                current_task,
                expected_id=expected_task.id,
                expected_name=expected_task.name,
                expected_type=expected_task.type,
                expected_status=expected_task.status,
                expected_day_id=expected_task.day_id,
            )