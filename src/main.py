import json

from flask import Flask
from flask import request

import entities
import repository
import migration

app = Flask(__name__)
migration.create_database_and_tables()
repository.set_zero_day()


@app.route("/api/tasks", methods=["POST"])
def create_task():
    request_body = request.get_json()

    if 'name' not in request_body:
        return json.dumps({'error': 'Field name is required'}), 400

    if len(request_body['name']) == 0:
        return json.dumps({'error': 'Field name cannot be empty'}), 400

    new_task = entities.Task(request_body['name'], 0, 'one-time', 'active')
    repository.insert_task(new_task)
    return json.dumps(new_task.to_dict()), 200


# @app.route("/api/day/current", methods=["GET"])
# def get_current_day():
#