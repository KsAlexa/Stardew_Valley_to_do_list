import sqlite3
from . import config

def create_database_and_tables():
    with sqlite3.connect(config.DB_PATH) as conn:
        cursor = conn.cursor()
        create_tasks_table_sql = """
                           create table if not exists main.tasks
                           (
                               id     INTEGER
                                   primary key autoincrement,
                               name   TEXT not null,
                               day_id integer,
                               type   TEXT NOT NULL CHECK (type IN ('dayly', 'one-time')),
                               status TEXT NOT NULL CHECK (type IN ('active', 'completed')),
                               FOREIGN KEY (day_id) REFERENCES days(id)
                           );
                           """
        cursor.execute(create_tasks_table_sql)

        create_days_table_sql = """
                           create table if not exists main.days
                           (
                               id     INTEGER
                                   primary key autoincrement,
                               year   integer,
                               season TEXT NOT NULL CHECK (season IN ('spring', 'summer', 'autumn', 'winter')),
                               number  integer, 
                               active BOOLEAN
                           );
                           """
        cursor.execute(create_days_table_sql)
        conn.commit()
