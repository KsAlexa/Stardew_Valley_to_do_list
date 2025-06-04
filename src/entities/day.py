class Day:
    def __init__(self, year: int, season: str, number: int, active: bool, day_id: int = None):
        self.id = day_id
        self.year = year
        self.season = season
        self.number = number
        self.active = active

    def to_dict(self):
        return {
            "id": self.id,
            "year": self.year,
            "season": self.season,
            "number": self.number,
            "active": self.active
        }