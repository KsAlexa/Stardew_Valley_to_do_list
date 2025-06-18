from src import repository, entities, errors
from .day_service import DayService


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

    def create_task(self, name: str):
        current_day = self.day_service.get_active()
        new_task = entities.Task(
            name=name,
            day_id=current_day.id,
            type='one-time',
            status='active'
        )
        self.task_repository.insert(new_task)
        return new_task

    def make_completed(self, id: int):
        current_day = self.day_service.get_active()
        task = self.get_by_id(id)

        if task.day_id != current_day.id:
            raise errors.InternalException(f'Task with ID {id} not found in current active day')
        if task.type != 'one-time':
            raise errors.InvalidTaskStateException(
                f'Task with ID {id} cannot be completed. Only \'one-time\' tasks can be marked as completed')
        if task.status == 'completed':
            raise errors.InvalidTaskStateException(f'Task with ID {id} is already completed.')

        self.task_repository.make_completed(id)
        updated_task = self.get_by_id(id)

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

        if task.day_id != current_day.id:
            raise errors.InternalException(f'Task with ID {id} not found in current active day')
        if task.status == 'completed':
            raise errors.InvalidTaskStateException(
                f'Task with ID {id} is completed. To make it a daily task, make it active first')

        self.task_repository.make_daily(id)
        updated_task = self.task_repository.get_by_id(id)
        return updated_task

    def make_one_time(self, id: int):
        current_day = self.day_service.get_active()
        task = self.get_by_id(id)

        if task.day_id != current_day.id:
            raise errors.InternalException(f'Task with ID {id} not found in active day')
        self.task_repository.make_one_time(id)
        updated_task = self.task_repository.get_by_id(id)
        return updated_task
