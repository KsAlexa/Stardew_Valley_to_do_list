import flask
from flask import Blueprint, request, json

from .models import CurrentDayResponse
from .. import repository
from .. import entities

day_bp = Blueprint('day_api', __name__, url_prefix='/api/day')


def _get_active_day_details():
    current_active_day = repository.get_active_day()
    if current_active_day is None:
        return None
    day_tasks = repository.get_tasks_by_day_id(current_active_day.id)
    current_day_details = CurrentDayResponse(
        day_id = current_active_day.id,
        year = current_active_day.year,
        season = current_active_day.season,
        number = current_active_day.number,
        tasks = day_tasks
    )
    return current_day_details


def _move_tasks_to_current_day(previous_active_day_id, next_active_day_id):
    previous_day_tasks = repository.get_tasks_by_day_id(previous_active_day_id)
    for task in previous_day_tasks:
        if task.type == 'daily':
            task.day_id = next_active_day_id
            repository.update_task_field(task.id, 'day_id', task.day_id)
        if task.type == 'one-time':
            task.status = 'completed'
            repository.update_task_field(task.id, 'status', task.status)


@day_bp.route("/current", methods=["GET"])
def get_current_day_info():
    current_day = _get_active_day_details()
    if current_day is None:
        return json.dumps({'error': 'No active day. Set a day first'}), 500

    return json.dumps(current_day.to_dict()), 200


@day_bp.route("/current", methods=["PUT"])
def set_current_day():
    request_body = request.get_json()

    # эту валидацию наверно надо че то куда то перенести
    required_fields = ['year', 'season', 'number']
    for field in required_fields:
        if field not in request_body:
            return json.dumps({'error': f'Field {field} is required'}), 400

    if not isinstance(request_body['year'], int) or request_body['year'] <= 0:
        return json.dumps({'error': 'Year must be a positive integer'}), 400

    if not isinstance(request_body['number'], int) or request_body['number'] <= 0 or request_body['number'] > 28:
        return json.dumps({'error': 'Number must be a positive integer between 1 and 28'}), 400

    if request_body['season'] not in ['spring', 'summer', 'autumn', 'winter']:
        return json.dumps({'error': 'Season must be spring, summer, autumn or winter'}), 400

    requested_day = entities.Day(
        year = request_body['year'],
        season = request_body['season'],
        number = request_body['number'],
        active = True
    )

    requested_day_from_db = repository.get_day_by_attributes(requested_day.year, requested_day.season, requested_day.number)
    previous_active_day = repository.get_active_day()

    if requested_day_from_db is None:
        repository.insert_day(requested_day)
        if previous_active_day:
            previous_active_day.active = False
            repository.update_day_active(previous_active_day)
            _move_tasks_to_current_day(previous_active_day.id, requested_day.id)
        requested_day_details = _get_active_day_details()
        # return flask.Response(json.dumps(requested_day_details.to_dict()), 201, mimetype="application/json")
        return json.dumps(requested_day_details.to_dict()), 201

    if previous_active_day and requested_day_from_db.id != previous_active_day.id:
        previous_active_day.active = False
        repository.update_day_active(previous_active_day)

    requested_day_from_db.active = True
    repository.update_day_active(requested_day_from_db)
    _move_tasks_to_current_day(previous_active_day.id, requested_day_from_db.id)
    requested_day_from_db_details = _get_active_day_details()
    return json.dumps(requested_day_from_db_details.to_dict()), 200


# надо при перелистывании дня оставлять tasks type == daily, а tasks type == one-time помечать завершенными make_task_completed()
@day_bp.route("/next", methods=["POST"])
def set_next_day():
    previous_active_day = repository.get_active_day()
    if previous_active_day is None:
        return json.dumps({'error': 'No active day set. Cannot define the next day.'}), 400

    next_day_year = previous_active_day.year
    next_day_season = previous_active_day.season
    next_day_number = previous_active_day.number + 1

    # и эту валидацию наверно надо куда то перенести
    max_day_per_season = 28
    seasons_order = ['spring', 'summer', 'autumn', 'winter']
    if next_day_number > max_day_per_season:
        next_day_number = 1
        next_day_season_index = seasons_order.index(next_day_season)
        if next_day_season_index == len(seasons_order) - 1:
            next_day_season = seasons_order[0]
            next_day_year += 1
        else:
            next_day_season = seasons_order[next_day_season_index + 1]

    next_day_from_db = repository.get_day_by_attributes(next_day_year, next_day_season, next_day_number)

    if next_day_from_db is None:
        previous_active_day.active = False
        repository.update_day_active(previous_active_day)
        next_day = entities.Day(
            year = next_day_year,
            season = next_day_season,
            number = next_day_number,
            active = True
        )
        repository.insert_day(next_day)
        _move_tasks_to_current_day(previous_active_day.id, next_day.id)
        next_day_details = _get_active_day_details()
        return json.dumps(next_day_details.to_dict()), 201

    previous_active_day.active = False
    repository.update_day_active(previous_active_day)
    next_day_from_db.active = True
    repository.update_day_active(next_day_from_db)
    _move_tasks_to_current_day(previous_active_day.id, next_day_from_db.id)
    next_day_from_db_details = _get_active_day_details()

    return json.dumps(next_day_from_db_details.to_dict()), 200