from typing import List

from src import entities


class CurrentDayResponse:
    def __init__(self, day_id: int, year: int, season: str, number: int, tasks: List[entities.Task]):
        self.id = day_id
        self.year = year
        self.season = season
        self.number = number
        self.active = True
        self.tasks = tasks

    def to_dict(self):
        tasks_list_as_dict = []
        for task_entity in self.tasks:
            tasks_list_as_dict.append(task_entity.to_dict())

        return {
            'id': self.id,
            'year': self.year,
            'season': self.season,
            'number': self.number,
            'active': self.active,
            'tasks': tasks_list_as_dict
        }