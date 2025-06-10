from flask import Blueprint, request, json
from src import repository
from src import entities
from .day import _get_active_day_details
from src.repository.task import _update_task_field

task_bp = Blueprint('task_api', __name__, url_prefix='/api/task')

@task_bp.route("", methods=["POST"])
def create_task():
    current_day = repository.get_active_day()

    if current_day is None:
        return json.dumps({'error': 'No active day set. Cannot add task'}), 400

    request_body = request.get_json()

    if 'name' not in request_body:
        return json.dumps({'error': 'Field name is required'}), 400

    if len(request_body['name']) == 0:
        return json.dumps({'error': 'Field name cannot be empty'}), 400

    new_task = entities.Task(
        name=request_body['name'],
        day_id=current_day.id,
        type='one-time',
        status='active'
    )
    repository.insert_task(new_task)
    return json.dumps(new_task.to_dict()), 200


@task_bp.route("/<int:id>/complete", methods=["PATCH"])
def complete_task(id):
    current_day = _get_active_day_details()
    if current_day is None:
        return json.dumps({'error': 'No active day set. Cannot update task'}), 400
    task_id = id
    is_task_found_in_current_day = False
    target_task_object = None
    for task in current_day.tasks:
        if task.id == task_id:
            is_task_found_in_current_day = True
            target_task_object = task
            break
    if not is_task_found_in_current_day:
            return json.dumps({'error': f'Task with ID {task_id} not found in current active day'}), 404
    if target_task_object.type != 'one-time':
        return json.dumps({'error': f'Task with ID {task_id} cannot be completed. Only \'one-time\' tasks can be marked as complete.'}), 400
    if target_task_object.status == 'completed':
        return json.dumps({'error': f'Task with ID {task_id} is already completed.'}), 400
    repository.make_task_completed(task_id)
    updated_task = repository.get_task_by_task_id(task_id)
    return json.dumps(updated_task.to_dict()), 200

@task_bp.route("/<int:id>/active", methods=["PATCH"])
def active(id):
    current_day = _get_active_day_details()
    if current_day is None:
        return json.dumps({'error': 'No active day set. Cannot update task'}), 400
    task_id = id
    target_task = repository.get_task_by_task_id(task_id)
    if target_task is None:
        return json.dumps({'error': f'Task with ID {task_id} not found'}), 404
    if target_task.status == 'active' and target_task.day_id == current_day.id:
        return json.dumps({'error': f'Task with ID {task_id} is already active.'}), 400
    repository.make_task_active(task_id)
    _update_task_field(task_id, 'day_id', current_day.id) # тут как лучше обновлять day_id у функции make_task_active или здесь вручную?
    updated_task = repository.get_task_by_task_id(task_id)
    return json.dumps(updated_task.to_dict()), 200


@task_bp.route("/<int:id>/daily", methods=["PATCH"])
def daily_task(id):
    current_day = _get_active_day_details()
    if current_day is None:
        return json.dumps({'error': 'No active day set. Cannot update task'}), 400
    task_id = id
    is_task_found_in_current_day = False
    target_task_object = None
    for task in current_day.tasks:
        if task.id == task_id:
            is_task_found_in_current_day = True
            target_task_object = task
            break
    if not is_task_found_in_current_day:
            return json.dumps({'error': f'Target task with ID {task_id} not found in current active day'}), 404
    if target_task_object.type == 'daily':
            return json.dumps(target_task_object.to_dict()), 200
    if target_task_object.status == 'completed':
        return json.dumps({'error': f'Task with ID {task_id} is completed. To make it a daily task, make it active first'}), 400
    repository.make_task_daily(task_id)
    updated_task = repository.get_task_by_task_id(task_id)
    return json.dumps(updated_task.to_dict()), 200



@task_bp.route("/<int:id>/one_time", methods=["PATCH"])
def one_time_task(id):
    current_day = _get_active_day_details()
    if current_day is None:
        return json.dumps({'error': 'No active day set. Cannot update task'}), 400
    task_id = id
    is_task_found_in_current_day = False
    target_task_object = None
    for task in current_day.tasks:
        if task.id == task_id:
            is_task_found_in_current_day = True
            target_task_object = task
            break
    if not is_task_found_in_current_day:
            return json.dumps({'error': f'Target task with ID {task_id} not found in current active day'}), 404
    if target_task_object.type == 'one-time' or target_task_object.status == 'completed':
        return json.dumps(target_task_object.to_dict()), 200
    repository.make_task_one_time(task_id)
    updated_task = repository.get_task_by_task_id(task_id)
    return json.dumps(updated_task.to_dict()), 200
