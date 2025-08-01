from enum import Enum
from typing import List
from src import entities
from pydantic import BaseModel, Field, ConfigDict


class DaySeason(str, Enum):
    spring = 'spring'
    summer = 'summer'
    autumn = 'autumn'
    winter = 'winter'


class TaskType(str, Enum):
    daily = 'daily'
    one_time = 'one-time'


class TaskStatus(str, Enum):
    active = 'active'
    completed = 'completed'


class TaskNameRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str = Field(min_length=1, description='Task name must have at least 1 character')


class TaskResponse(BaseModel):
    id: int
    name: str
    type: TaskType
    day_id: int
    status: TaskStatus

    @classmethod
    def from_task(cls, task: entities.Task) -> 'TaskResponse':
        return cls(
            id=task.id,
            name=task.name,
            type=TaskType(task.type),
            day_id=task.day_id,
            status=TaskStatus(task.status)
        )


class SetCurrentDayRequest(BaseModel):
    year: int = Field(gt=0, description='Year must be a positive integer')
    season: DaySeason
    number: int = Field(gt=0, le=28, description='Number must be a positive integer between 1 and 28')


class CurrentDayResponse(BaseModel):
    id: int
    year: int
    season: DaySeason
    number: int
    active: bool
    tasks: List[TaskResponse] | None = None

    @classmethod
    def from_day(cls, day: entities.Day, tasks: List[entities.Task] | None) -> 'CurrentDayResponse':
        task_responses = [TaskResponse.from_task(task) for task in tasks]
        return cls(
            id=day.id,
            year=day.year,
            season=DaySeason(day.season),
            number=day.number,
            active=day.active,
            tasks=task_responses
        )


class CurrentStateResponse(BaseModel):
    current_day_info: CurrentDayResponse
    all_completed_tasks: List[TaskResponse]

    @classmethod
    def from_entities(cls, current_day: entities.Day, day_tasks: List[entities.Task],
                      completed_tasks: List[entities.Task]) -> 'CurrentStateResponse':

        current_day_response = CurrentDayResponse.from_day(current_day, day_tasks)
        completed_tasks_response = [TaskResponse.from_task(task) for task in completed_tasks]
        return cls(
            current_day_info=current_day_response,
            all_completed_tasks=completed_tasks_response
        )
