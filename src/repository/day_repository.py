import sqlite3
from .. import entities
from ..errors import MultipleActiveDaysException


class DayRepository:

    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    def insert(self, day: entities.Day):
        with sqlite3.connect(self.connection_string) as conn:
            cursor = conn.cursor()
            insert_sql = """
                         INSERT INTO days (year, season, number, active)
                         VALUES (?, ?, ?, ?)
                         ON CONFLICT(year, season, number) DO NOTHING;
                         """
            data = (day.year, day.season, day.number, day.active)
            cursor.execute(insert_sql, data)
            conn.commit()
            day.id = cursor.lastrowid

    def get_active(self) -> entities.Day | None:
        with sqlite3.connect(self.connection_string) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            select_active_day_sql = """
                                    SELECT *
                                    FROM days
                                    WHERE active = 1; \
                                    """
            cursor.execute(select_active_day_sql)
            day_data = cursor.fetchall()
            if not day_data:
                return None
            if len(day_data) > 1:
                raise MultipleActiveDaysException(message='Multiple active days')
            return entities.Day(
                day_id=day_data[0]['id'],
                year=day_data[0]['year'],
                season=day_data[0]['season'],
                number=day_data[0]['number'],
                active=bool(day_data[0]['active'])
            )

    def get_by_id(self, day_id: int) -> entities.Day | None:
        with sqlite3.connect(self.connection_string) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            select_day_by_id_sql = """
                                   SELECT *
                                   FROM days
                                   WHERE id = ?; \
                                   """
            data = (day_id,)
            cursor.execute(select_day_by_id_sql, data)
            day_data = cursor.fetchone()
            if day_data is None:
                return None
            return entities.Day(
                day_id=day_data['id'],
                year=day_data['year'],
                season=day_data['season'],
                number=day_data['number'],
                active=bool(day_data['active'])
            )

    def get_by_attributes(self, year: int, season: str, number: int) -> entities.Day | None:
        with sqlite3.connect(self.connection_string) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            select_day_by_attributes_sql = """
                                           SELECT *
                                           FROM days
                                           WHERE year = ?
                                             AND season = ?
                                             AND number = ?; \
                                           """
            data = (year, season, number)
            cursor.execute(select_day_by_attributes_sql, data)
            day_data = cursor.fetchone()
            if day_data is None:
                return None
            return entities.Day(
                day_id=day_data['id'],
                year=day_data['year'],
                season=day_data['season'],
                number=day_data['number'],
                active=bool(day_data['active'])
            )

    def set_activity(self, day_id: int, active: bool):
        with sqlite3.connect(self.connection_string) as conn:
            cursor = conn.cursor()
            update_day_active_sql = """
                                    UPDATE days
                                    SET active = ?
                                    WHERE id = ?; \
                                    """
            data = (active, day_id)
            cursor.execute(update_day_active_sql, data)
            conn.commit()
