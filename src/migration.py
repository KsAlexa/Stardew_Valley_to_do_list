import sqlite3
import config

def create_database_and_table():
    with sqlite3.connect(config.DB_PATH) as conn:
        cursor = conn.cursor()
        create_table_sql = """
                           create table main.tasks
                           (
                               id     INTEGER
                                   primary key autoincrement,
                               name   TEXT not null,
                               day_id integer,
                               type   TEXT,
                               status TEXT
                           );
                           """
        cursor.execute(create_table_sql)
        conn.commit()
