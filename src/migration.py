import sqlite3


def create_database_and_tables(db_path: str):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        create_tasks_table_sql = """
                                 create table if not exists main.tasks
                                 (
                                     id     INTEGER PRIMARY KEY AUTOINCREMENT,
                                     name   TEXT    NOT NULL,
                                     day_id INTEGER NOT NULL CHECK (day_id > 0),
                                     type   TEXT    NOT NULL CHECK (type IN ('daily', 'one-time')),
                                     status TEXT    NOT NULL CHECK (status IN ('active', 'completed')),
                                     FOREIGN KEY (day_id) REFERENCES days (id),
                                     UNIQUE (name)
                                 ); \
                                 """
        create_tasks_uniq_index_sql = """ \
                                      create unique index if not exists tasks_name_uindex
                                          on tasks (name); \
                                      """
        create_days_table_sql = """
                                create table if not exists main.days
                                (
                                    id     INTEGER PRIMARY KEY AUTOINCREMENT,
                                    year   INTEGER NOT NULL CHECK (year > 0),
                                    season TEXT    NOT NULL CHECK (season IN ('spring', 'summer', 'autumn', 'winter')),
                                    number INTEGER NOT NULL CHECK (number BETWEEN 1 AND 28),
                                    active BOOLEAN NOT NULL,
                                    UNIQUE (year, season, number)
                                ); \
                                """
        create_days_uniq_index_sql = """create unique index if not exists days_season_year_number_uindex
            on days (season, year, number); \
                                     """

        cursor.execute(create_tasks_table_sql)
        cursor.execute(create_days_table_sql)
        cursor.execute(create_days_uniq_index_sql)
        cursor.execute(create_tasks_uniq_index_sql)

        cursor.execute("SELECT COUNT(*) FROM main.days")
        row = cursor.fetchone()
        if row[0] == 0:
            cursor.execute("""
                           INSERT INTO main.days (year, season, number, active)
                           VALUES (1, 'spring', 1, 1); \
                           """)
        conn.commit()
