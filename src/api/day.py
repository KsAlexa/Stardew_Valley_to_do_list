from flask import Blueprint, request, json
from .. import repository
from .. import entities

day_bp = Blueprint('day_api', __name__, url_prefix='/api/day')


def _get_current_display_day():
    current_display_day = repository.get_active_day()
    if current_display_day is None:
        current_display_day = repository.get_zero_day()
        if current_display_day is None:
            return json.dumps({'error': 'Zero day not found'}), 500
    return current_display_day


@day_bp.route("/current", methods=["GET"])
def get_current_day_info():
    current_day = _get_current_display_day()

    is_zero_day = (current_day.year == 0 and
                   current_day.number == 0 and
                   current_day.season == 'undefined')

    day_info = current_day.to_dict()
    day_info['tasks'] = []

    if is_zero_day:
        day_info['tasks'] = []
        day_info['message'] = 'Set a day first'
    elif not is_zero_day and not current_day.active:
            day_info['tasks'] = []
            day_info['message'] = 'Day is not active'
    elif not is_zero_day and current_day.active:
            tasks_list = repository.get_tasks_by_day_id(current_day.id)
            day_info['tasks'] = [task.to_dict() for task in tasks_list]
    return json.dumps(day_info), 200

@day_bp.route("/current", methods=["PUT"])
def set_current_day():
    request_body = request.get_json()

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

    target_day = repository.get_day_by_attributes(request_body['year'], request_body['season'], request_body['number'])
    previous_active_day = repository.get_active_day()

    if target_day is None:
        new_day = entities.Day(year=request_body['year'], season=request_body['season'], number=request_body['number'], active=True)
        repository.insert_day(new_day)
        if previous_active_day:
            previous_active_day.active = False
            repository.update_day_active(previous_active_day)
        return json.dumps(new_day.to_dict()), 200

    if previous_active_day and target_day.id != previous_active_day.id:
        previous_active_day.active = False
        repository.update_day_active(previous_active_day)

    target_day.active = True
    repository.update_day_active(target_day)
    return json.dumps(target_day.to_dict()), 200





# @day_bp.route("/next", methods=["POST"])
# def next_day():
#     current_day = _get_current_display_day()