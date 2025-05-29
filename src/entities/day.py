class Day:
    def __init__(self, year: int, season: str, number: int, tasks: list, active: bool, day_id: int = None):
        self.id = day_id
        self.year = year
        self.season = season
        self.number = number
        self.tasks = tasks
        self.active = active
