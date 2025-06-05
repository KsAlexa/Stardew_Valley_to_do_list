from flask import Flask
from . import migration
from . api import *

app = Flask(__name__)
migration.create_database_and_tables()


app.register_blueprint(day_bp)
app.register_blueprint(task_bp)

if __name__ == '__main__':
    app.run(debug=True)