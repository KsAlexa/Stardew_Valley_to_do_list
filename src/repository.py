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