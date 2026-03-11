import sqlite3

DB_NAME = "workouts.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS workouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                exercise TEXT,
                duration INTEGER,
                notes TEXT
            )
        """)
        conn.commit()


def add_workout(date, exercise, duration, notes):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO workouts (date, exercise, duration, notes) VALUES (?, ?, ?, ?)",
            (date, exercise, duration, notes)
        )
        conn.commit()


def get_all_workouts():
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT id, date, exercise, duration, notes FROM workouts ORDER BY id DESC"
        )
        return cursor.fetchall()
