from flask import Blueprint, request, json
from src import repository
from src import entities
from .day import _get_active_day_details

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