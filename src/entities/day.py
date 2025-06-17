from typing import List

from src import entities


class Day:
    def __init__(self, year: int, season: str, number: int, active: bool, day_id: int = None):
        self.id = day_id
        self.year = year
        self.season = season
        self.number = number
        self.active = active