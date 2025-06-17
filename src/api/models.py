from enum import Enum
from typing import List
from src import entities
from pydantic import BaseModel, Field, ConfigDict


class AddTaskRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str = Field(min_length=1)


class TaskResponse(BaseModel):
    id: int
    name: str
    type: str
    day_id: int
    status: str

    @classmethod
    def from_task(cls, task: entities.Task) -> 'TaskResponse':
        return cls(
            id=task.id,
            name=task.name,
            type=task.type,
            day_id=task.day_id,
            status=task.status
        )


class Season(str, Enum):
    spring = 'spring'
    summer = 'summer'
    autumn = 'autumn'
    winter = 'winter'


class SetCurrentDayRequest(BaseModel):
    year: int = Field(gt=0, description='Year must be a positive integer')
    season: Season
    number: int = Field(gt=0, le=28, description='Number must be a positive integer between 1 and 28')


class DayResponse(BaseModel):
    id: int
    year: int
    season: str
    number: int
    active: bool
    tasks: List[TaskResponse] | None = None
