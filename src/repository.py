import entities
import sqlite3
import config

def insert_task(task: entities.Task):
    with sqlite3.connect(config.DB_PATH) as conn:
        cursor = conn.cursor()
        insert_sql = """
                     INSERT INTO tasks (name, day_id, type, status)
                     VALUES (?, ?, ?, ?);
                     """
        data = (task.name, task.day_id, task.type, task.status)
        cursor.execute(insert_sql, data)
        conn.commit()
        task.id = cursor.lastrowid


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

def set_zero_day(day: entities.Day):
    with sqlite3.connect(config.DB_PATH) as conn:
        cursor = conn.cursor()
        select_zero_day_sql = """
                SELECT id FROM days 
                WHERE year = ? AND number = ? AND season = ?;
                """
        data = (0, 0, 'undefined')
        cursor.execute(select_zero_day_sql, data)
        existing_day_id = cursor.fetchone()
        if existing_day_id is None:
            zero_day = entities.Day(year=0, season='undefined', number=0, active=False)
            insert_day(zero_day)


# def get_active_day():
#
# def get_day_by_id(day_id: int):
