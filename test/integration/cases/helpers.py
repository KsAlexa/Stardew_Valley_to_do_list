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
