from flask import Flask
import repository
import migration
from api.day import day_bp
from api.task import task_bp

app = Flask(__name__)
migration.create_database_and_tables()
repository.set_zero_day()


app.register_blueprint(day_bp)
app.register_blueprint(task_bp)


if __name__ == '__main__':
    app.run(debug=True)
