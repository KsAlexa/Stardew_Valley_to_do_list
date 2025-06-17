from fastapi import FastAPI
# import logging
from . import migration
from . api import *

app = FastAPI()
migration.create_database_and_tables()


app.include_router(day.router)
app.include_router(task.router)

# logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#
# if __name__ == '__main__':
#     app.run(debug=True)