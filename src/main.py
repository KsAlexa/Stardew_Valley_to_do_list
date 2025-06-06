from flask import Flask
import logging
from . import migration
from . api import *

app = Flask(__name__)
migration.create_database_and_tables()


app.register_blueprint(day_bp)
app.register_blueprint(task_bp)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

if __name__ == '__main__':
    app.run(debug=True)