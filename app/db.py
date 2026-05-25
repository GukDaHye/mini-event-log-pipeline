import time

import psycopg2
from psycopg2.extras import RealDictCursor, execute_values

from app.config import DB_CONFIG


EVENT_COLUMNS = (
    "event_type",
    "user_id",
    "session_id",
    "event_time",
    "page_url",
    "product_id",
    "quantity",
    "amount",
    "error_code",
    "error_message",
)


def connect(max_attempts=20, delay_seconds=0.5):
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            return psycopg2.connect(**DB_CONFIG)
        except psycopg2.OperationalError as exc:
            last_error = exc
            if attempt == max_attempts:
                break
            time.sleep(delay_seconds)
    raise RuntimeError("could not connect to PostgreSQL") from last_error


def reset_events(conn):
    with conn.cursor() as cursor:
        cursor.execute("TRUNCATE TABLE events RESTART IDENTITY;")
    conn.commit()


def insert_events(conn, events):
    if not events:
        return

    values = [tuple(event[column] for column in EVENT_COLUMNS) for event in events]
    columns = ", ".join(EVENT_COLUMNS)

    with conn.cursor() as cursor:
        execute_values(
            cursor,
            f"INSERT INTO events ({columns}) VALUES %s",
            values,
            page_size=500,
        )
    conn.commit()


def fetch_all(conn, sql, params=None):
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]
