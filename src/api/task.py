import flask
from flask import Blueprint, request, json
from .. import repository, config, services, errors
from .day import _get_active_day_details

task_bp = Blueprint('task_api', __name__, url_prefix='/api/task')

day_repository = repository.DayRepository(config.DB_PATH)
task_repository = repository.TaskRepository(config.DB_PATH)
day_service = services.DayService(day_repository, task_repository)
task_service = services.TaskService(task_repository, day_repository)

@task_bp.route("", methods=["POST"])
def create_task_handle():
    request_body = request.get_json()

    if 'name' not in request_body:
        return json.dumps({'error': 'Field name is required'}), 400

    if len(request_body['name']) == 0:
        return json.dumps({'error': 'Field name cannot be empty'}), 400

    try:
        new_task = task_service.create_task(request_body['name'])
    except errors.NotFoundException as e:
        return json.dumps({'error': e.message}), 404

    return flask.Response(json.dumps(new_task.to_dict()), 200, mimetype="application/json")


@task_bp.route("/<int:id>/complete", methods=["PATCH"])
def make_task_complete_handle(id):
    try:
        task_service.make_task_complete(id)
    except errors.NotFoundException as e:
        return json.dumps({'error': e.message}), 404
    except errors.InvalidStateException as e:
        return json.dumps({'error': e.message}), 400

    return "", 200

@task_bp.route("/<int:id>/active", methods=["PATCH"])
def make_task_active_handle(id):
    try:
        task_service.make_task_active(id)
    except errors.NotFoundException as e:
        return json.dumps({'error': e.message}), 404
    except errors.InvalidStateException as e:
        return json.dumps({'error': e.message}), 400

    return "", 200


@task_bp.route("/<int:id>/daily", methods=["PATCH"])
def make_task_daily_handle(id):
    try:
        task_service.make_task_daily(id)
    except errors.NotFoundException as e:
        return json.dumps({'error': e.message}), 404
    except errors.InvalidStateException as e:
        return json.dumps({'error': e.message}), 400

    return "", 200


@task_bp.route("/<int:id>/one_time", methods=["PATCH"])
def make_task_one_time_handle(id):
    try:
        task_service.make_task_one_time(id)
    except errors.NotFoundException as e:
        return json.dumps({'error': e.message}), 404

    return "", 200
