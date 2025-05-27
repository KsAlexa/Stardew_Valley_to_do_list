from flask import Flask, jsonify
from flask import request
import sqlite3

app = Flask(__name__)

DB_PATH = "../db/todo_list.sqlite"


class Task:
    id: int
    name: str
    day_id: int
    type: str
    status: str


# CLASS_NAME
# CLASS_FIELDS
# CLASS_

class Name:
    pass


class CreateTaskRequest:
    name: str

    def __init__(self, name: str):
        self.name = name


class CreateTaskResponse:
    id: int
    name: str
    type: str
    status: str


@app.route("/api/tasks", methods=["POST"])
def create_task():
    request_body = request.get_json()
    if 'name' not in request_body:
        return jsonify({"error": "Поле 'name' обязательно"}), 400

    create_task_request = CreateTaskRequest(name=request_body['name'])
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        insert_sql = """
                     INSERT INTO tasks (name)
                     VALUES (?);
                     """
        data = (create_task_request.name,)
        cursor.execute(insert_sql, data)
        conn.commit()
        return "", 200


def create_database_and_table():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        create_table_sql = """
                           CREATE TABLE IF NOT EXISTS tasks
                           (
                               id   INTEGER PRIMARY KEY AUTOINCREMENT,
                               name TEXT NOT NULL
                           );
                           """
        cursor.execute(create_table_sql)
        conn.commit()
