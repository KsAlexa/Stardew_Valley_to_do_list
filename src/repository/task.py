import sqlite3
import logging
from .. import entities
from .. import config


logger = logging.getLogger(__name__)


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


def get_tasks_by_day_id(day_id: int) -> list | None:
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


def get_task_by_task_id(task_id: int) -> entities.Task | None:
    with sqlite3.connect(config.DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        select_task_by_id_sql = """
            SELECT * FROM tasks
            WHERE id = ?;
        """
        data = (task_id,)
        cursor.execute(select_task_by_id_sql, data)
        task_data = cursor.fetchone()
        if task_data is None:
            return None
        return entities.Task(
            task_id = task_data['id'],
            name = task_data['name'],
            type = task_data['type'],
            status = task_data['status'],
            day_id = task_data['day_id']
        )


def _update_task_field(task_id: int, field_name: str, new_value: str):
    if field_name not in ('status', 'type'):
        logger.error(f'Attempt to update invalid field \'{field_name}\' for task ID {task_id}. Valid fields are \'status\', \'type\'.')
        return
    #try:
    with sqlite3.connect(config.DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        update_task_field_sql = f"""
            UPDATE tasks
            SET {field_name} = ?
            WHERE id = ?;
        """
        data = (new_value, task_id)
        cursor.execute(update_task_field_sql, data)
        conn.commit()
#       logging.info(f"Поле '{field_name}' задачи с ID {task_id} успешно обновлено.")
#         return True
#    except sqlite3.Error as e:
#       logging.error(f"Ошибка SQLite при обновлении поля '{field_name}' задачи {task_id}: {e}")
#       return False
#     except Exception as e:
#         logging.error(f"Непредвиденная ошибка при обновлении поля '{field_name}' задачи {task_id}: {e}")
#         return False



def make_task_completed(task_id: int):
    target_task = get_task_by_task_id(task_id)
    if target_task is None:
        return None
    target_task.status = 'completed'
    _update_task_field(task_id, 'status', target_task.status)



def make_task_uncompleted(task_id: int):
    target_task = get_task_by_task_id(task_id)
    if target_task is None:
        return None
    target_task.status = 'uncompleted'
    _update_task_field(task_id, 'status', target_task.status)
