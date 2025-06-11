import sqlite3
from .. import entities
from .. import config


def insert_task(task: entities.Task):
    with sqlite3.connect(config.DB_PATH) as conn:
        cursor = conn.cursor()
        insert_task_sql = """
                          INSERT INTO tasks (name, day_id, type, status)
                          VALUES (?, ?, ?, ?); \
                          """
        data = (task.name, task.day_id, task.type, task.status)
        cursor.execute(insert_task_sql, data)
        conn.commit()
        task.id = cursor.lastrowid


def get_tasks_by_day_id(day_id: int) -> list:
    with sqlite3.connect(config.DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        select_tasks_for_day_sql = """
                                   SELECT *
                                   FROM tasks
                                   WHERE day_id = ?; \
                                   """
        data = (day_id,)
        cursor.execute(select_tasks_for_day_sql, data)
        tasks_data = cursor.fetchall()
        tasks = []
        if tasks_data is None:
            return tasks
        for task_data in tasks_data:
            tasks.append(entities.Task(
                task_id=task_data['id'],
                name=task_data['name'],
                day_id=task_data['day_id'],
                type=task_data['type'],
                status=task_data['status']
            ))
        return tasks


def get_task_by_task_id(task_id: int) -> entities.Task | None:
    with sqlite3.connect(config.DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        select_task_by_id_sql = """
                                SELECT *
                                FROM tasks
                                WHERE id = ?; \
                                """
        data = (task_id,)
        cursor.execute(select_task_by_id_sql, data)
        task_data = cursor.fetchone()
        if task_data is None:
            return None
        return entities.Task(
            task_id=task_data['id'],
            name=task_data['name'],
            type=task_data['type'],
            status=task_data['status'],
            day_id=task_data['day_id']
        )


def update_task_field(task_id: int, field_name: str, new_value):
    # if field_name not in ('status', 'type'):
    #     logger.error(f'Attempt to update invalid field \'{field_name}\' for task ID {task_id}. Valid fields are \'status\', \'type\'.')
    #     return False
    # if field_name == 'status' and new_value not in ('active', 'completed'):
    #     logger.error(f'Attempt to pass invalid value \'{new_value}\' of field \'{field_name}\' for task ID {task_id}. Valid values are \'active\', \'completed\'.')
    #     return False
    # elif field_name == 'type' and new_value not in ('daily', 'one-time'):
    #     logger.error(f'Attempt to pass invalid value \'{new_value}\' of field \'{field_name}\' for task ID {task_id}. Valid values are \'daily\', \'one-time\'.')
    #     return False

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


def make_task_completed(task_id: int):
    target_task = get_task_by_task_id(task_id)
    if target_task is None:
        raise Exception("target task not found")
    target_task.status = 'completed'
    update_task_field(task_id, 'status', target_task.status)


def make_task_active(task_id: int, task_day_id: int):
    target_task = get_task_by_task_id(task_id)
    if target_task is None:
        raise Exception("target task not found")
    target_task.status = 'active'
    update_task_field(task_id, 'status', target_task.status)
    update_task_field(task_id, 'day_id', task_day_id)

def make_task_daily(task_id: int):
    target_task = get_task_by_task_id(task_id)
    if target_task is None:
        raise Exception("target task not found")
    target_task.type = 'daily'
    update_task_field(task_id, 'type', target_task.type)

def make_task_one_time(task_id: int):
    target_task = get_task_by_task_id(task_id)
    if target_task is None:
        raise Exception("target task not found")
    target_task.type = 'one-time'
    update_task_field(task_id, 'type', target_task.type)



