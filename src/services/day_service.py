from src import repository, entities, errors


class DayService:
    seasons = ['spring', 'summer', 'autumn', 'winter']
    max_day_per_season = 28

    def __init__(self, day_repository: repository.DayRepository, task_repository: repository.TaskRepository):
        self.day_repository = day_repository
        self.task_repository = task_repository

    def get_active(self):
        active_day = self.day_repository.get_active()
        if active_day is None:
            raise errors.InternalException('No active day')
        return active_day

    def set_current_day(self, year: int, season: str, number: int):
        previous_active_day = self.get_active()

        if not isinstance(year, int) or year <= 0:
            raise errors.InvalidDayError(f'Year must be a positive integer, but got {year}')
        if season not in self.seasons:
            raise errors.InvalidDayError(f'Season must be one of {self.seasons}, but got "{season}"')
        if not isinstance(number, int) or not (1 <= number <= self.max_day_per_season):
            raise errors.InvalidDayError(f'Day number must be an integer between 1 and {self.max_day_per_season}, but got {number}')

        self._change_active_day(previous_active_day, year, season, number)

    def set_next_day(self):
        previous_active_day = self.get_active()

        next_day_year = previous_active_day.year
        next_day_season = previous_active_day.season
        next_day_number = previous_active_day.number + 1

        if next_day_number > self.max_day_per_season:
            next_day_number = 1
            next_day_season_index = self.seasons.index(next_day_season)
            if next_day_season_index == len(self.seasons) - 1:
                next_day_season = self.seasons[0]
                next_day_year += 1
            else:
                next_day_season = self.seasons[next_day_season_index + 1]

        self._change_active_day(previous_active_day, next_day_year, next_day_season, next_day_number)

    def _change_active_day(self, previous_active_day: entities.Day, year: int, season: str, number: int):
        if (previous_active_day.year == year and
                previous_active_day.season == season and
                previous_active_day.number == number):
            return

        self.day_repository.set_activity(previous_active_day.id, False)

        new_active_day = self.day_repository.get_by_attributes(year = year, season = season, number = number)

        if new_active_day is None:
            new_active_day = entities.Day(year = year, season = season, number = number, active=True)
            try:
                self.day_repository.insert(new_active_day)
            except errors.DuplicateDayException:
                raise
        else:
            self.day_repository.set_activity(new_active_day.id, True)

        self._move_tasks_to_current_day(previous_active_day.id, new_active_day.id)

    def _move_tasks_to_current_day(self, previous_active_day_id, next_active_day_id):
        previous_day_tasks = self.task_repository.get_all_by_day_id(previous_active_day_id)
        for task in previous_day_tasks:
            if task.type == 'daily':
                task.day_id = next_active_day_id
                self.task_repository.update_field(task.id, 'day_id', task.day_id)
            if task.type == 'one-time' and task.status == 'active':
                task.status = 'completed'
                self.task_repository.update_field(task.id, 'status', task.status)
