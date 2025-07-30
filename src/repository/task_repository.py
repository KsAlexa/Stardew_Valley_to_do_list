import sqlite3
from .. import entities
from typing import List
from ..errors import DuplicateTaskNameException


class TaskRepository:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    def insert(self, task: entities.Task):
        with sqlite3.connect(self.connection_string) as conn:
            cursor = conn.cursor()
            insert_task_sql = """
                              INSERT INTO tasks (name, day_id, type, status)
                              VALUES (?, ?, ?, ?);
                              """
            data = (task.name, task.day_id, task.type, task.status)
            try:
                cursor.execute(insert_task_sql, data)
                conn.commit()
                task.id = cursor.lastrowid
                return task
            except sqlite3.IntegrityError:
                raise DuplicateTaskNameException(
                    f'Task with name "{task.name}" already exists'
                )

    def get_all_by_day_id(self, day_id: int) -> List[entities.Task]:
        with sqlite3.connect(self.connection_string) as conn:
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
            for task_data in tasks_data:
                tasks.append(entities.Task(
                    task_id=task_data['id'],
                    name=task_data['name'],
                    day_id=task_data['day_id'],
                    type=task_data['type'],
                    status=task_data['status']
                ))
            return tasks

    def get_by_id(self, task_id: int) -> entities.Task | None:
        with sqlite3.connect(self.connection_string) as conn:
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

    def get_all_completed(self)-> List[entities.Task]:
        with sqlite3.connect(self.connection_string) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            select_all_completed_tasks_sql = """
                                       SELECT *
                                       FROM tasks
                                       WHERE status = 'completed'; \
                                       """
            cursor.execute(select_all_completed_tasks_sql)
            tasks_data = cursor.fetchall()
            tasks = []
            for task_data in tasks_data:
                tasks.append(entities.Task(
                    task_id=task_data['id'],
                    name=task_data['name'],
                    day_id=task_data['day_id'],
                    type=task_data['type'],
                    status=task_data['status']
                ))
            return tasks

    def update_field(self, task_id: int, field_name: str, new_value):
        allowed_fields = ['name', 'status', 'type', 'day_id']
        if field_name not in allowed_fields:
            raise ValueError(f'Field "{field_name}" cannot be modified')

        with sqlite3.connect(self.connection_string) as conn:
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

    def make_completed(self, task_id: int):
        self.update_field(task_id, 'status', 'completed')

    def make_active(self, task_id: int, task_day_id: int):
        self.update_field(task_id, 'status', 'active') # TODO: make it one database query
        self.update_field(task_id, 'day_id', task_day_id)

    def make_daily(self, task_id: int):
        self.update_field(task_id, 'type', 'daily')

    def make_one_time(self, task_id: int):
        self.update_field(task_id, 'type', 'one-time')

    def edit_name(self, task_id: int, new_name: str):
        self.update_field(task_id, 'name', new_name)
