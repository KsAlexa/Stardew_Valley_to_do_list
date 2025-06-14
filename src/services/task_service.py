import json

from src import repository, entities, errors
from src.api import task_repository


class TaskService:
    def __init__(self, task_repository: repository.TaskRepository, day_repository: repository.DayRepository):
        self.day_repository = day_repository
        self.task_repository = task_repository

    def get_all_by_day_id(self, day_id: int):
        return self.task_repository.get_all_by_day_id(day_id)

    def create_task(self, name: str):
        current_day = self.day_repository.get_active()

        if current_day is None:
            raise errors.NotFoundException('No active day set. Cannot add task')

        new_task = entities.Task(
            name = name,
            day_id = current_day.id,
            type = 'one-time',
            status = 'active'
        )
        self.task_repository.insert(new_task)
        return new_task

    def make_task_complete(self, id: int):
        current_day = self.day_repository.get_active()

        if current_day is None:
            raise errors.NotFoundException('No active day set. Cannot update task')

        day_tasks = task_repository.get_all_by_day_id(current_day.id)

        task_id = id
        is_task_found_in_current_day = False
        target_task_object = None
        for task in day_tasks:
            if task.id == task_id:
                is_task_found_in_current_day = True
                target_task_object = task
                break
        if not is_task_found_in_current_day:
            raise errors.NotFoundException(f'Task with ID {task_id} not found in current active day')
        if target_task_object.type != 'one-time':
            raise errors.InvalidStateException(f'Task with ID {task_id} cannot be completed. Only \'one-time\' tasks can be marked as complete')
        if target_task_object.status == 'completed':
            raise errors.InvalidStateException(f'Task with ID {task_id} is already completed.')
        task_repository.make_completed(task_id)
        # updated_task = task_repository.get_by_id(task_id)
        # return updated_task

    def make_task_active(self, id: int):
        current_day = self.day_repository.get_active()

        if current_day is None:
            raise errors.NotFoundException('No active day set. Cannot update task')

        task_id = id
        target_task = task_repository.get_by_id(task_id)
        if target_task is None:
            raise errors.NotFoundException(f'Task with ID {task_id} not found')
        if target_task.status == 'active' and target_task.day_id == current_day.id:
            raise errors.InvalidStateException(f'Task with ID {task_id} is already active.')
        task_repository.make_active(task_id, current_day.id)
        # updated_task = task_repository.get_by_id(task_id)
        # return updated_task

    def make_task_daily(self, id: int):
        current_day = self.day_repository.get_active()

        if current_day is None:
            raise errors.NotFoundException('No active day set. Cannot update task')

        day_tasks = task_repository.get_all_by_day_id(current_day.id)

        task_id = id
        is_task_found_in_current_day = False
        target_task_object = None
        for task in day_tasks:
            if task.id == task_id:
                is_task_found_in_current_day = True
                target_task_object = task
                break
        if not is_task_found_in_current_day:
            raise errors.NotFoundException(f'Task with ID {task_id} not found in current active day')
        if target_task_object.status == 'completed':
            raise errors.InvalidStateException(f'Task with ID {task_id} is completed. To make it a daily task, make it active first')
        task_repository.make_daily(task_id)
        # updated_task = task_repository.get_by_id(task_id)
        # return updated_task


    def make_task_one_time(self, id: int):
        current_day = self.day_repository.get_active()

        if current_day is None:
            raise errors.NotFoundException('No active day set. Cannot update task')

        day_tasks = task_repository.get_all_by_day_id(current_day.id)

        task_id = id
        is_task_found_in_current_day = False
        for task in day_tasks:
            if task.id == task_id:
                is_task_found_in_current_day = True
                break
        if not is_task_found_in_current_day:
            raise errors.NotFoundException(f'Task with ID {task_id} not found in current active day')
        task_repository.make_one_time(task_id)
        # updated_task = task_repository.get_by_id(task_id)
        # return updated_task
