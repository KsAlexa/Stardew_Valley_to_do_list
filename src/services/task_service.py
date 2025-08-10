from src import repository, entities, errors
from .day_service import DayService
from typing import List


class TaskService:
    def __init__(self, task_repository: repository.TaskRepository, day_service: DayService):
        self.day_service = day_service
        self.task_repository = task_repository

    def get_all_by_day_id(self, day_id: int):
        return self.task_repository.get_all_by_day_id(day_id)

    def get_by_id(self, id: int) -> entities.Task:
        task = self.task_repository.get_by_id(id)
        if task is None:
            raise errors.TaskNotFoundException(f'Task with id {id} not found')
        return task

    def get_all_completed(self) -> List[entities.Task]:
        return self.task_repository.get_all_completed()

    def create_task(self, name: str):
        current_day = self.day_service.get_active()
        new_task = entities.Task(
            name=name,
            day_id=current_day.id,
            type='one-time',
            status='active'
        )
        try:
            created_task = self.task_repository.insert(new_task)
            return created_task
        except errors.DuplicateTaskNameException:
            raise

    def make_completed(self, id: int):
        current_day = self.day_service.get_active()
        task = self.get_by_id(id)

        self._check_task_in_current_day(task, current_day)
        if task.type != 'one-time':
            raise errors.InvalidTaskStateException(
                f'Task with ID {id} cannot be completed. Only \'one-time\' tasks can be marked as completed')
        if task.status == 'completed':
            raise errors.InvalidTaskStateException(f'Task with ID {id} is already completed.')

        self.task_repository.make_completed(id)
        updated_task = self.get_by_id(id)  ## нужен ли повторный запрос к бд или лучше изменять объект в памяти? task.status = 'completed' return task

        return updated_task

    def make_active(self, id: int):
        current_day = self.day_service.get_active()
        task = self.get_by_id(id)

        if task.status == 'active' and task.day_id == current_day.id:
            raise errors.InvalidTaskStateException(f'Task with ID {id} is already active.')

        self.task_repository.make_active(id, current_day.id)
        updated_task = self.task_repository.get_by_id(id)
        return updated_task

    def make_daily(self, id: int):
        current_day = self.day_service.get_active()
        task = self.get_by_id(id)

        self._check_task_in_current_day(task, current_day)
        if task.status == 'completed':
            raise errors.InvalidTaskStateException(
                f'Task with ID {id} is completed. To make it a daily task, make it active first')
        if task.type == 'daily':
            raise errors.InvalidTaskStateException(f'Task with ID {id} is already a daily task.')

        self.task_repository.make_daily(id)
        updated_task = self.task_repository.get_by_id(id)
        return updated_task

    def make_one_time(self, id: int):
        current_day = self.day_service.get_active()
        task = self.get_by_id(id)

        self._check_task_in_current_day(task, current_day)

        if task.status == 'completed':
            raise errors.InvalidTaskStateException(f'Task with ID {id} is completed.')
        if task.type == 'one-time':
            raise errors.InvalidTaskStateException(f'Task with ID {id} is already a one-time task.')

        self.task_repository.make_one_time(id)
        updated_task = self.task_repository.get_by_id(id)
        return updated_task

    def edit_name(self, id: int, new_name: str):
        current_day = self.day_service.get_active()
        task = self.get_by_id(id)

        self._check_task_in_current_day(task, current_day)
        if task.status == 'completed':
            raise errors.InvalidTaskStateException(
                f'Task with ID {id} is completed. To edit it, make it active first.')
        try:
            self.task_repository.edit_name(id, new_name)
            updated_task = self.task_repository.get_by_id(id)
            return updated_task
        except errors.DuplicateTaskNameException:
            raise

    def _check_task_in_current_day(self, task: entities.Task, day: entities.Day):
        if task.day_id != day.id:
            raise errors.TaskNotInActiveDayError(
                f"Task with ID {task.id} not found in active day {day.id}"
            )
