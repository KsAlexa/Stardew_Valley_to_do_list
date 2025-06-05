from .. import entities
import sqlite3
from .. import config


def insert_day(day: entities.Day):
    with sqlite3.connect(config.DB_PATH) as conn:
        cursor = conn.cursor()
        insert_sql = """
                     INSERT INTO days (year, season, number, active)
                     VALUES (?, ?, ?, ?);
                     """
        data = (day.year, day.season, day.number, 1 if day.active else 0)
        cursor.execute(insert_sql, data)
        conn.commit()
        day.id = cursor.lastrowid

# def set_zero_day():
#     with sqlite3.connect(config.DB_PATH) as conn:
#         cursor = conn.cursor()
#         select_zero_day_sql = """
#                 SELECT id FROM days
#                 WHERE year = ? AND number = ? AND season = ?;
#                 """
#         data = (0, 0, 'undefined')
#         cursor.execute(select_zero_day_sql, data)
#         existing_day_id = cursor.fetchone()
#         if existing_day_id is None:
#             zero_day = entities.Day(year=0, season='undefined', number=0, active=False)
#             insert_day(zero_day)
#
#
# def get_zero_day():
#     with sqlite3.connect(config.DB_PATH) as conn:
#         conn.row_factory = sqlite3.Row
#         cursor = conn.cursor()
#         select_zero_day_sql = """
#             SELECT * FROM days
#             WHERE year = ? AND number = ? AND season = ?;
#             """
#         data = (0, 0, 'undefined')
#         cursor.execute(select_zero_day_sql, data)
#         day_data = cursor.fetchone()
#         if day_data is None:
#             return None
#         return entities.Day(
#             day_id = day_data['id'],
#             year = day_data['year'],
#             season = day_data['season'],
#             number = day_data['number'],
#             active = bool(day_data['active'])
#             )


def get_active_day():
    with sqlite3.connect(config.DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        select_active_day_sql = """
            SELECT * FROM days
            WHERE active = 1;
        """
        cursor.execute(select_active_day_sql)
        day_data = cursor.fetchone()
        if day_data is None:
            return None
        return entities.Day(
            day_id = day_data['id'],
            year = day_data['year'],
            season = day_data['season'],
            number = day_data['number'],
            active = bool(day_data['active'])
            )

def get_day_by_id(day_id: int):
    with sqlite3.connect(config.DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        select_day_by_id_sql = """
            SELECT * FROM days
            WHERE id = ?;
        """
        data = (day_id,)
        cursor.execute(select_day_by_id_sql, data)
        day_data = cursor.fetchone()
        if day_data is None:
            return None
        return entities.Day(
            day_id = day_data['id'],
            year = day_data['year'],
            season = day_data['season'],
            number = day_data['number'],
            active = bool(day_data['active'])
            )

def get_day_by_attributes(year: int, season: str, number: int):
    with sqlite3.connect(config.DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        select_day_by_attributes_sql = """
            SELECT * FROM days
            WHERE year = ? AND season = ? AND number = ?;
        """
        data = (year, season, number)
        cursor.execute(select_day_by_attributes_sql, data)
        day_data = cursor.fetchone()
        if day_data is None:
            return None
        return entities.Day(
            day_id = day_data['id'],
            year = day_data['year'],
            season = day_data['season'],
            number = day_data['number'],
            active = bool(day_data['active'])
            )

def update_day_active(day: entities.Day):
    with sqlite3.connect(config.DB_PATH) as conn:
        cursor = conn.cursor()
        update_day_active_sql = """
            UPDATE days
            SET active = ?
            WHERE id = ?;
        """
        data = (day.active, day.id)
        cursor.execute(update_day_active_sql, data)
        conn.commit()