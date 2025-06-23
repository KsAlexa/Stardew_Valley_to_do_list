from src import repository, entities
from src.errors import InternalException


class DayService:
    def __init__(self, day_repository: repository.DayRepository, task_repository: repository.TaskRepository):
        self.day_repository = day_repository
        self.task_repository = task_repository

    def get_active(self):
        active_day = self.day_repository.get_active()
        if active_day is None:
            raise InternalException('No active day')
        return active_day

    def set_current_day(self, year: int, season: str, number: int):
        previous_active_day = self.get_active()

        self.day_repository.set_activity(previous_active_day.id, False)

        new_active_day = self.day_repository.get_by_attributes(year, season, number)

        if new_active_day is None:
            new_active_day = entities.Day(year, season, number, active=True)
            self.day_repository.insert(new_active_day)
            self._move_tasks_to_current_day(previous_active_day.id, new_active_day.id)
            return

        if new_active_day.id == previous_active_day.id:
            return

        self.day_repository.set_activity(new_active_day.id, True)
        self._move_tasks_to_current_day(previous_active_day.id, new_active_day.id)

    def set_next_day(self):
        previous_active_day = self.get_active()

        next_day_year = previous_active_day.year
        next_day_season = previous_active_day.season
        next_day_number = previous_active_day.number + 1

        max_day_per_season = 28
        seasons_order = ['spring', 'summer', 'autumn', 'winter']
        if next_day_number > max_day_per_season:
            next_day_number = 1
            next_day_season_index = seasons_order.index(next_day_season)
            if next_day_season_index == len(seasons_order) - 1:
                next_day_season = seasons_order[0]
                next_day_year += 1
            else:
                next_day_season = seasons_order[next_day_season_index + 1]

        self.day_repository.set_activity(previous_active_day.id, False)
        next_active_day = self.day_repository.get_by_attributes(next_day_year, next_day_season, next_day_number)

        if next_active_day is None:
            next_active_day = entities.Day(
                year=next_day_year,
                season=next_day_season,
                number=next_day_number,
                active=True
            )
            self.day_repository.insert(next_active_day)
            self._move_tasks_to_current_day(previous_active_day.id, next_active_day.id)
            return

        self.day_repository.set_activity(next_active_day.id, True)
        self._move_tasks_to_current_day(previous_active_day.id, next_active_day.id)

    def _move_tasks_to_current_day(self, previous_active_day_id, next_active_day_id):
        previous_day_tasks = self.task_repository.get_all_by_day_id(previous_active_day_id)
        for task in previous_day_tasks:
            if task.type == 'daily':
                task.day_id = next_active_day_id
                self.task_repository.update_field(task.id, 'day_id', task.day_id)
            if task.type == 'one-time':
                task.status = 'completed'
                self.task_repository.update_field(task.id, 'status', task.status)
