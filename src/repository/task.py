from .. import entities
import sqlite3
from .. import config

def insert_task(task: entities.Task):
    with sqlite3.connect(config.DB_PATH) as conn:
        cursor = conn.cursor()
        insert_task_sql = """
                     INSERT INTO tasks (name, day_id, type, status)
                     VALUES (?, ?, ?, ?);
                     """
        data = (task.name, task.day_id, task.type, task.status)
        cursor.execute(insert_task_sql, data)
        conn.commit()
        task.id = cursor.lastrowid


def get_tasks_by_day_id(day_id: int):
    with sqlite3.connect(config.DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        select_tasks_for_day_sql = """
            SELECT * FROM tasks
            WHERE day_id = ?;
        """
        data = (day_id,)
        cursor.execute(select_tasks_for_day_sql, data)
        tasks_data = cursor.fetchall()
        tasks = []
        for task_data in tasks_data:
            tasks.append(entities.Task(
                task_id = task_data['id'],
                name = task_data['name'],
                day_id = task_data['day_id'],
                type = task_data['type'],
                status = task_data['status']
                ))
        return tasks