class Day:
    def __init__(self, year: int, season: str, number: int, active: bool, day_id: int = None):
        self.id = day_id
        self.year = year
        self.season = season
        self.number = number
        self.active = active

    def __eq__(self, other):
        if not isinstance(other, Day):
            return NotImplemented
        return (self.id == other.id and
                self.year == other.year and
                self.season == other.season and
                self.number == other.number and
                self.active == other.active)