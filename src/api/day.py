from flask import Blueprint, request, json

from .models import CurrentDayResponse
from .. import repository, config, services, errors

day_bp = Blueprint('day_api', __name__, url_prefix='/api/day')

day_repository = repository.DayRepository(config.DB_PATH)
task_repository = repository.TaskRepository(config.DB_PATH)
day_service = services.DayService(day_repository, task_repository)
task_service = services.TaskService(task_repository, day_repository)


def _get_active_day_details():
    current_active_day = day_service.get_active()
    if current_active_day is None:
        return None
    day_tasks = task_service.get_all_by_day_id(current_active_day.id)
    current_day_details = CurrentDayResponse(
        day_id=current_active_day.id,
        year=current_active_day.year,
        season=current_active_day.season,
        number=current_active_day.number,
        tasks=day_tasks
    )
    return current_day_details


@day_bp.route("/current", methods=["GET"])
def get_current_day_info_handle():
    current_day = _get_active_day_details()
    if current_day is None:
        return json.dumps({'error': 'No active day. Set a day first'}), 500

    return json.dumps(current_day.to_dict()), 200


@day_bp.route("/current", methods=["PUT"])
def set_current_day_handle():
    request_body = request.get_json()

    # эту валидацию наверно надо че то куда то перенести
    # note: from yaroslav, use Pydantic models to validate fields and accept requests
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

    year = request_body['year']
    season = request_body['season']
    number = request_body['number']
    day_service.set_current_day(year, season, number)

    return "", 200


# надо при перелистывании дня оставлять tasks type == daily, а tasks type == one-time помечать завершенными make_task_completed()
@day_bp.route("/next", methods=["POST"])
def set_next_day_handle():
    try:
        day_service.set_next_day()
    except errors.NotFoundException as e:
        return json.dumps({'error': e.message}), 404
    return "", 200
