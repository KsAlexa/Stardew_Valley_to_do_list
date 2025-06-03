from flask import Blueprint, request, json
from .. import repository
from ..import entities

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